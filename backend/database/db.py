"""
db.py
-----
Handles the raw SQLite connection and table creation.

We are using plain sqlite3 (not an ORM like SQLAlchemy) on purpose:
- It's beginner-friendly and transparent — you can see the actual SQL
- SQLite is a single file database, perfect for a hackathon project
- No extra server/setup needed
"""

import sqlite3
import os
from config import Config


def get_db_connection():
    """
    Opens a new connection to the SQLite database.
    Each request gets its own connection - this is the safe way
    to use SQLite in a web app (connections aren't shared across requests).
    """
    # Make sure the 'database' folder exists before connecting
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)

    conn = sqlite3.connect(Config.DATABASE_PATH)

    # This makes rows behave like dictionaries (row["title"] instead of row[0])
    # Much more readable than plain tuples.
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Creates the 'notes' table if it doesn't already exist.
    Called once when the app starts up.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source_type TEXT NOT NULL,       -- 'pdf' or 'text'
            filename TEXT,                   -- original filename if PDF, else NULL
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            due_date TEXT NOT NULL,          -- stored as 'YYYY-MM-DD'
            status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' or 'completed'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized (notes + assignments tables ready)")