#database_manager.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "pantun.db")

def get_connection():
    return sqlite3.connect(DB_PATH)


# 🟩 Fetch all pantuns
def get_all_pantuns():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT p.pantun_id, p.title, p.tags, p.line1, p.line2, p.line3, p.line4, u.username
        FROM pantun p
        LEFT JOIN users u ON p.user_id = u.user_id
        ORDER BY p.pantun_id DESC
    """)
    rows = c.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def add_pantun(title, tags, lines, user_id=0):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO pantun (title, tags, line1, line2, line3, line4, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, tags, lines[0], lines[1], lines[2], lines[3], user_id))
    conn.commit()
    conn.close()


# 🟥 Delete pantun by ID
def delete_pantun(pantun_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM pantun WHERE pantun_id = ?", (pantun_id,))
    conn.commit()
    conn.close()


# 🟦 Fetch pantun lines for rhyme analysis
def get_pantun_by_id(pantun_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT line1, line2, line3, line4
        FROM pantun
        WHERE pantun_id = ?
    """, (pantun_id,))
    row = c.fetchone()
    conn.close()

    if row:
        return [row["line1"], row["line2"], row["line3"], row["line4"]]
    return None

# Pantun Rating Table Functions
def add_pantun_rating(pantun_id, user_id, rating):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO pantun_rating (pantun_id, user_id, rating)
        VALUES (?, ?, ?)
    """, (pantun_id, user_id, rating))
    conn.commit()
    conn.close()

def add_pantun_to_db(data):
    conn = get_connection()
    c = conn.cursor()

    # Ensure lines are split individually
    line1 = data.get("line1", "")
    line2 = data.get("line2", "")
    line3 = data.get("line3", "")
    line4 = data.get("line4", "")

    c.execute("""
        INSERT INTO pantun (title, user_id, tags, line1, line2, line3, line4)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("title", ""),
        data.get("user_id", 0),  # <-- changed from username
        data.get("tags", ""),
        line1, line2, line3, line4
    ))

    pantun_id = c.lastrowid
    conn.commit()
    conn.close()
    return pantun_id



