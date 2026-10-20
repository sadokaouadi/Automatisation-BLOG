import sqlite3
from pathlib import Path


DB_PATH = Path("data/database/orders.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    return connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

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

    connection.commit()
    connection.close()