#database_setup.py

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "pantun.db")

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # USER TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL
    )
    """)

    # PANTUN TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS pantun (
        pantun_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        tags TEXT,
        line1 TEXT,
        line2 TEXT,
        line3 TEXT,
        line4 TEXT,
        user_id INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)

    # PANTUN CLASS TABLE (Tutorial / Textbook)
    c.execute("""
    CREATE TABLE IF NOT EXISTS pantun_class (
        class_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL
    )
    """)


    # USER ↔ PANTUN CLASS (INTERMEDIARY TABLE)
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_pantun_class (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        class_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (class_id) REFERENCES pantun_class(class_id)
    )
    """)

    # PANTUN RATING TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS pantun_rating (
        rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
        pantun_id INTEGER,
        user_id INTEGER,

        rating INTEGER CHECK(rating >= 1 AND rating <= 5),  -- ⭐ final rating (1–5)
        auto_score INTEGER,                                                -- raw calculated score

        syllable_line1 INTEGER,
        syllable_line2 INTEGER,
        syllable_line3 INTEGER,
        syllable_line4 INTEGER,

        rhyme_type TEXT,                 -- e.g. "ABAB", "AAAA", "AABB", "None"
        moral_detected INTEGER DEFAULT 0 CHECK(moral_detected IN (0,1)),   -- 1 = Yes, 0 = No
        all_lines_filled INTEGER DEFAULT 0 CHECK(all_lines_filled IN (0,1)),

        FOREIGN KEY (pantun_id) REFERENCES pantun(pantun_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)



    # INSERT DEFAULT GUEST USER
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (0, 'GUEST')")

    conn.commit()
    conn.close()
    print("✅ All tables created successfully!")

if __name__ == "__main__":
    create_tables()
