import sqlite3
import os
DB_PATH = "C:/Users/user/Desktop/.../database/pantun.db"  # exact path printed by Flask
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT * FROM pantun")
rows = c.fetchall()
print(rows)
conn.close()
