from database.database import get_connection

def drop_hardcoded_tables():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = OFF")

        cursor.execute("DROP TABLE IF EXISTS cards_translations")
        cursor.execute("DROP TABLE IF EXISTS cards")
        cursor.execute("DROP TABLE IF EXISTS deck_contents")
        cursor.execute("DROP TABLE IF EXISTS duelist_deck_translations")
        cursor.execute("DROP TABLE IF EXISTS duelist_decks")
        cursor.execute("DROP TABLE IF EXISTS deck_category_translations")
        cursor.execute("DROP TABLE IF EXISTS deck_categories")
        cursor.execute("DROP TABLE IF EXISTS duelists")

        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
    finally:
        conn.close()