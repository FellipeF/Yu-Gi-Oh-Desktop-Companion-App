import sqlite3

DB_NAME = "cards.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY,
        name TEXT,
        name_en TEXT,
        type TEXT,
        attribute TEXT,
        atk INTEGER,
        def INTEGER,
        level INTEGER
    )
    """)

    conn.commit()
    conn.close()
