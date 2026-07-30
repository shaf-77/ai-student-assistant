"""
assignment.py
-------------
Model layer for assignments -- same pattern as models/note.py.
Routes call these functions instead of writing raw SQL directly.
"""

from database.db import get_db_connection


def create_assignment(title, subject, due_date):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO assignments (title, subject, due_date, status)
        VALUES (?, ?, ?, 'pending')
        """,
        (title, subject, due_date)
    )

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_all_assignments():
    """
    Returns all assignments sorted by due_date ascending,
    so the most urgent ones appear first.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM assignments ORDER BY due_date ASC")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_assignment_by_id(assignment_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def update_assignment_status(assignment_id, status):
    """
    Toggles an assignment between 'pending' and 'completed'.
    Returns True if a row was actually updated, False if the ID didn't exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE assignments SET status = ? WHERE id = ?",
        (status, assignment_id)
    )

    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_assignment(assignment_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))

    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted