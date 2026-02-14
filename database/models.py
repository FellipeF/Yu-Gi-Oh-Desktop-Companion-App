import sqlite3

import api_client
from database.database import get_connection

def populate_cards():
    data = api_client.load_cards()
    cards = data["data"]

    conn = get_connection()
    cursor = conn.cursor()

    for card in cards:
        cursor.execute("""
        INSERT OR IGNORE INTO cards (id, name, name_en, type, attribute, atk, def, level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            card.get("id"),
            card.get("name"),
            card.get("name_en"),
            card.get("type"),
            card.get("attribute"),
            card.get("atk"),
            card.get("def"),
            card.get("level")
            )
        )

    conn.commit()
    conn.close()

def search_cards(name=None):
    conn = sqlite3.connect("cards.db")
    cursor = conn.cursor()

    query = ("SELECT id, name, name_en "
             "FROM cards "
             "WHERE 1=1")
    params = []

    if name:
        query += " AND (LOWER(name) LIKE LOWER(?) OR LOWER(name_en) LIKE LOWER(?))"
        params.extend([f"%{name}%", f"%{name}%"])

    query += " ORDER BY name COLLATE NOCASE"

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    return results
