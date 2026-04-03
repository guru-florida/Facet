import os
import sqlite3
from app.config import settings


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    os.makedirs(os.path.dirname(os.path.abspath(settings.db_path)), exist_ok=True)
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS identities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                identity_id TEXT NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
                embedding BLOB NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
    finally:
        conn.close()
