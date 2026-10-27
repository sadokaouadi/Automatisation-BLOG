from PyQt6.QtCore import QThread, pyqtSignal

from app.services.outlook_reader import (
    download_new_pdf_attachments
)

from app.services.order_intake_service import (
    prepare_order_from_pdf
)


class OutlookMonitorWorker(QThread):

    order_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):

        try:

            attachments = (
                download_new_pdf_attachments()
            )

            for attachment in attachments:

                try:

                    pdf_path = attachment[
                        "local_path"
                    ]

                    order = (
                        prepare_order_from_pdf(
                            pdf_path
                        )
                    )

                    # Informations Outlook
                    order["outlook_subject"] = (
                        attachment.get(
                            "subject",
                            ""
                        )
                    )

                    order["outlook_sender"] = (
                        attachment.get(
                            "sender",
                            ""
                        )
                    )

                    order["outlook_received_time"] = (
                        attachment.get(
                            "received_time",
                            ""
                        )
                    )

                    self.order_ready.emit(
                        order
                    )

                except Exception as exc:

                    self.error.emit(
                        f"Erreur extraction PDF : {exc}"
                    )

        except Exception as exc:

            self.error.emit(
                f"Erreur Outlook : {exc}"
            )