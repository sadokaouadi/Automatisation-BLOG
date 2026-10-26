from pathlib import Path
import re

import pythoncom
import win32com.client

from app.database.database import (
    create_tables,
    is_outlook_attachment_processed,
    mark_outlook_attachment_processed,
)


MAX_EMAILS_TO_CHECK = 30

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTLOOK_DOWNLOAD_DIR = (
    PROJECT_ROOT
    / "data"
    / "uploads"
    / "outlook"
)


def clean_filename(filename):
    """
    Nettoie le nom d'une pièce jointe Outlook.
    """

    filename = Path(
        str(filename)
    ).name

    filename = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        filename
    )

    return filename


def download_new_pdf_attachments(
    max_emails=MAX_EMAILS_TO_CHECK
):
    """
    Cherche les emails Outlook récents.

    Télécharge uniquement les PDF
    qui n'ont jamais été traités.
    """

    create_tables()

    OUTLOOK_DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    pythoncom.CoInitialize()

    try:

        outlook = (
            win32com.client.Dispatch(
                "Outlook.Application"
            )
        )

        namespace = outlook.GetNamespace(
            "MAPI"
        )

        # 6 = Inbox
        inbox = namespace.GetDefaultFolder(
            6
        )

        messages = inbox.Items

        # Plus récent en premier
        messages.Sort(
            "[ReceivedTime]",
            True
        )

        checked = 0

        for message in messages:

            if checked >= max_emails:
                break

            checked += 1

            try:

                # Outlook MailItem
                if message.Class != 43:
                    continue

                entry_id = str(
                    message.EntryID or ""
                )

                if not entry_id:
                    continue

                subject = str(
                    message.Subject or ""
                )

                sender = str(
                    message.SenderName or ""
                )

                received_time = str(
                    message.ReceivedTime
                )

                attachment_count = (
                    message.Attachments.Count
                )

                for index in range(
                    1,
                    attachment_count + 1
                ):

                    attachment = (
                        message.Attachments.Item(
                            index
                        )
                    )

                    filename = str(
                        attachment.FileName or ""
                    )

                    if not filename.lower().endswith(
                        ".pdf"
                    ):
                        continue

                    # Déjà traité ?
                    if is_outlook_attachment_processed(
                        entry_id,
                        filename
                    ):
                        continue

                    safe_name = clean_filename(
                        filename
                    )

                    # EntryID ajouté au nom
                    # pour éviter les collisions.
                    short_id = entry_id[-12:]

                    local_path = (
                        OUTLOOK_DOWNLOAD_DIR
                        / f"{short_id}_{safe_name}"
                    )

                    attachment.SaveAsFile(
                        str(local_path)
                    )

                    mark_outlook_attachment_processed(
                        entry_id,
                        filename,
                        local_path
                    )

                    results.append({
                        "entry_id": entry_id,
                        "subject": subject,
                        "sender": sender,
                        "received_time":
                            received_time,

                        "attachment_name":
                            filename,

                        "local_path":
                            str(local_path),
                    })

            except Exception as exc:

                print(
                    "[WARNING] Mail ignoré :",
                    exc
                )

        return results

    finally:

        pythoncom.CoUninitialize()


if __name__ == "__main__":

    print()
    print("==============================")
    print("CHECK OUTLOOK")
    print("==============================")

    try:

        results = (
            download_new_pdf_attachments()
        )

        print(
            "Nouveaux PDF :",
            len(results)
        )

        for item in results:

            print()
            print(
                "Sujet :",
                item["subject"]
            )

            print(
                "Expéditeur :",
                item["sender"]
            )

            print(
                "PDF :",
                item["attachment_name"]
            )

            print(
                "Sauvegardé :",
                item["local_path"]
            )

    except Exception as exc:

        print(
            "[ERREUR]",
            exc
        )