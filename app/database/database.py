import sqlite3
from pathlib import Path


DB_PATH = Path("data/database/orders.db")


# =========================================================
# CONNEXION SQLITE
# =========================================================

def get_connection():
    """
    Ouvre la connexion vers la base SQLite locale.
    """

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DB_PATH
    )

    return connection


# =========================================================
# CREATION DES TABLES
# =========================================================

def create_tables():
    """
    Crée les tables principales si elles n'existent pas.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # -----------------------------------------------------
    # COMMANDES
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            date TEXT,
            customer_date TEXT,

            po TEXT NOT NULL,
            product TEXT NOT NULL,

            quantity INTEGER,
            length REAL,
            upc TEXT,

            customer TEXT,

            status TEXT DEFAULT 'A_VERIFIER',

            verification_1 INTEGER DEFAULT 0,
            verification_2 INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------------------------------
    # PIECES JOINTES OUTLOOK DEJA TRAITEES
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outlook_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            outlook_entry_id TEXT NOT NULL,
            attachment_name TEXT NOT NULL,
            local_path TEXT,

            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(
                outlook_entry_id,
                attachment_name
            )
        )
    """)

    connection.commit()
    connection.close()


# =========================================================
# OUTLOOK - VERIFIER SI PDF DEJA TRAITE
# =========================================================

def is_outlook_attachment_processed(
    entry_id,
    attachment_name
):
    """
    Retourne True si cette pièce jointe Outlook
    a déjà été téléchargée / traitée.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM outlook_attachments
        WHERE outlook_entry_id = ?
          AND attachment_name = ?
        LIMIT 1
    """, (
        entry_id,
        attachment_name
    ))

    result = cursor.fetchone()

    connection.close()

    return result is not None


# =========================================================
# OUTLOOK - MARQUER PDF COMME TRAITE
# =========================================================

def mark_outlook_attachment_processed(
    entry_id,
    attachment_name,
    local_path
):
    """
    Enregistre une pièce jointe Outlook
    pour éviter de la traiter plusieurs fois.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO outlook_attachments (
            outlook_entry_id,
            attachment_name,
            local_path
        )
        VALUES (?, ?, ?)
    """, (
        entry_id,
        attachment_name,
        str(local_path)
    ))

    connection.commit()
    connection.close()


# =========================================================
# TEST SIMPLE
# =========================================================

if __name__ == "__main__":

    create_tables()

    print(
        "Base SQLite initialisee :",
        DB_PATH
    )