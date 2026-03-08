import sqlite3
from database.database import get_connection
from database.database import DB_NAME
from data.duelists_decks_translations import DECK_SPECIFIC_TRANSLATION

def search_cards(name=None, language="en"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        SELECT cards.id, cards_translations.name
        FROM cards
        JOIN cards_translations
        ON cards.id = cards_translations.card_id
        WHERE cards_translations.language = ?
    """
    params = [language]

    #When we're searching cards on the CardsFrame, the results are filtered with the current typed letters on the
    #searchbox

    if name:
        query += " AND LOWER(cards_translations.name) LIKE LOWER(?)"
        params.append(f"%{name}%")

    query += " ORDER BY cards_translations.name COLLATE NOCASE"

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    return results

def get_all_duelists():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, name, img_path
    FROM duelists
    ORDER BY name
    """)

    results = cursor.fetchall()
    conn.close()
    return results

def populate_deck_translations():
    """Translate Duelists Specific Deck"""
    conn = get_connection()
    cursor = conn.cursor()

    for duelist_name, deck_name_en, lang, translated in DECK_SPECIFIC_TRANSLATION:
        cursor.execute("SELECT id FROM duelists WHERE name = ?", (duelist_name,))
        duelist = cursor.fetchone()
        if not duelist:
            continue

        cursor.execute("SELECT id FROM decks where duelist_id = ? AND name = ?", (duelist[0], deck_name_en))
        deck = cursor.fetchone()
        if not deck:
            continue

        cursor.execute("""
            INSERT OR IGNORE INTO decks_translations (deck_id, language, name) 
            VALUES (?, ?, ?)
        """, (deck[0], lang, translated))

    conn.commit()
    conn.close()

def get_decks_by_duelist(duelist_id, language="en", show_exclusive_cards=True):
    conn = get_connection()
    cursor = conn.cursor()

    #Order decks and fetches cards from DB on one query only.
    query = """
        SELECT
        d.id AS deck_id,
        COALESCE(dttr_lang.name, dttr_en.name, dtr_lang.name, dtr_en.name, d.name) AS deck_name,
        d.order_index AS deck_order,
        dc.card_id,
        COALESCE(ct_lang.name, ct_en.name, dc.card_name) AS card_name,
        dc.quantity
        FROM decks d
        LEFT JOIN decks_translations dtr_lang
        ON dtr_lang.deck_id = d.id
        AND dtr_lang.language = :lang
        LEFT JOIN decks_translations dtr_en
        ON dtr_en.deck_id = d.id
        AND dtr_en.language = 'en'
        LEFT JOIN deck_types dt
        ON dt.id = d.deck_type_id
        LEFT JOIN deck_type_translation dttr_lang
        ON dttr_lang.deck_type_id = dt.id
        AND dttr_lang.language = :lang
        LEFT JOIN deck_type_translation dttr_en
        ON dttr_en.deck_type_id = dt.id
        AND dttr_en.language = 'en'
        LEFT JOIN deck_cards dc
        ON dc.deck_id = d.id
    """

    # checkbox filter, controlled by Duelist Details Frame
    if not show_exclusive_cards:
        query += " AND dc.card_id IS NOT NULL\n"

    query += """
        LEFT JOIN cards c
        ON c.id = dc.card_id
        LEFT JOIN cards_translations ct_lang
        ON ct_lang.card_id = c.id
        AND ct_lang.language = :lang
        LEFT JOIN cards_translations ct_en
        ON ct_en.card_id = c.id
        AND ct_en.language = 'en'
        WHERE d.duelist_id = :duelist_id
        ORDER BY
        d.order_index,
        card_name COLLATE NOCASE
    """

    cursor.execute(query, {"lang": language, "duelist_id": duelist_id})
    rows = cursor.fetchall()
    conn.close()

    decks = []
    by_deck = {}

    for (deck_id, deck_name, _deck_order,
         card_id, card_name, qty) in rows:

        if deck_id not in by_deck:
            obj = {"deck_id": deck_id, "deck_name": deck_name, "cards": []}
            by_deck[deck_id] = obj
            decks.append(obj)

        #TODO: Take this out after testing, decks should never be empty on the final version.
        if qty is not None:
            by_deck[deck_id]["cards"].append((card_id, card_name, qty))

    return decks

def get_card_details(card_id: int, language="en"):
    """When card is selected on DuelistDetailsFrame or CardsFrame, user can verify additional info on the card"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id,
            COALESCE(ct_lang.name, ct_en.name) AS name,
            COALESCE(ct_lang.description, ct_en.description, '') AS description,
            c.atk,
            c.def,
            c.type
        FROM cards c
        LEFT JOIN cards_translations ct_lang
            ON ct_lang.card_id = c.id AND ct_lang.language = ?
        LEFT JOIN cards_translations ct_en
            ON ct_en.card_id = c.id AND ct_en.language = 'en'
        WHERE c.id = ?
        LIMIT 1
    """, (language, card_id))

    row = cursor.fetchone()
    conn.close()
    return row