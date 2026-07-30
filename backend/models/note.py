"""
note.py
-------
This is our 'Note' model — a thin layer between the database
and the rest of the app. Routes should NEVER write raw SQL directly;
they call these functions instead. This keeps app logic organized
and makes it easy to change the database later without touching routes.
"""

from database.db import get_db_connection


def create_note(title, content, source_type, filename=None):
    """
    Inserts a new note into the database.
    Returns the newly created note's ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO notes (title, content, source_type, filename)
        VALUES (?, ?, ?, ?)
        """,
        (title, content, source_type, filename)
    )

    conn.commit()
    new_id = cursor.lastrowid   # ID of the row we just inserted
    conn.close()

    return new_id


def get_all_notes():
    """
    Returns all notes, most recent first.
    Used for displaying the notes list in the dashboard.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notes ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    # Convert sqlite3.Row objects into plain dictionaries (easier to send as JSON)
    return [dict(row) for row in rows]


def get_note_by_id(note_id):
    """
    Fetches a single note by its ID.
    Will be used heavily in Feature 2 (Q&A) and Feature 3 (Summarize).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None
def delete_note(note_id):
    """
    Deletes a note from the database.
    Returns True if a row was actually deleted, False if the ID didn't exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))

    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted