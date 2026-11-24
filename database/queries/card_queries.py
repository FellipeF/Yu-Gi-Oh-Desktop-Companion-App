from database.database import get_connection
from models.card import CardDetails

def search_cards(name: str | None = None, language: str = "en") -> list[tuple]:
    """Search cards, filtered by language. Also implements fallback in case selected language doesn't have a translation
    for the card"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT cards.id, 
            COALESCE (cards_translations_lang.name, cards_translations_en.name) AS resolved_name
        FROM cards
        LEFT JOIN cards_translations AS cards_translations_lang
            ON cards.id = cards_translations_lang.card_id
            AND cards_translations_lang.language_code = ?
        LEFT JOIN cards_translations AS cards_translations_en
            ON cards.id = cards_translations_en.card_id
            AND cards_translations_en.language_code = 'en'
        WHERE COALESCE (cards_translations_lang.name, cards_translations_en.name) IS NOT NULL
    """
    params = [language]

    if name:
        query += " AND COALESCE (cards_translations_lang.name, cards_translations_en.name) LIKE ? COLLATE NOCASE"
        params.append(f"%{name}%")

    query += " ORDER BY COALESCE (cards_translations_lang.name, cards_translations_en.name) COLLATE NOCASE"

    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        conn.close()

def get_card_details(card_id: int, language_code="en"):
    """When card is selected on the Frame, user can check additional info, like stats and description"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                c.id,
                COALESCE(ct_lang.name, ct_en.name) AS name,
                COALESCE(ct_lang.description, ct_en.description, '') AS description,
                c.type,
                c.readablecardtype,
                c.race,
                c.attribute,
                c.atk,
                c.def,
                c.level,
                c.scale,
                c.linkval,
                c.linkmarkers
            FROM cards c
            LEFT JOIN cards_translations ct_lang
                ON ct_lang.card_id = c.id
                AND ct_lang.language_code = ?
            LEFT JOIN cards_translations ct_en
                ON ct_en.card_id = c.id
                AND ct_en.language_code = 'en'
            WHERE c.id = ?
            LIMIT 1
            """,
            (language_code, card_id),
        )
        return cursor.fetchone()
    finally:
        conn.close()

def get_cards_count() -> int:
    """Counts all cards present in the database"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM cards")
        return cursor.fetchone()[0]
    finally:
        conn.close()

def get_card_details_model(card_id: int, language_code: str = "en") -> CardDetails | None:
    row = get_card_details(card_id, language_code)
    return CardDetails(*row) if row is not None else None
#TODO: Work with dataclasses instead of  tuples