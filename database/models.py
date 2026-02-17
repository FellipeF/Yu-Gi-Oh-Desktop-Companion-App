import sqlite3
import api_client
from database.database import get_connection
from database.deck_data import DECKS_DATA
from database.database import DB_NAME

ARC_NAMES = {
    "Toei - First Series",
    "Toei - Death-T",
    "Toei - Movie",
    "Duelist Kingdom",
    #TODO: Add More in the future
}

def populate_cards(language="en"):
    """Inserts cards and their translation into Database"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1
        FROM cards_translation
        WHERE language = ?
        LIMIT 1
    """, (language, ))

    exists = cursor.fetchone()

    if exists:
        conn.close()
        return

    data = api_client.load_cards(language)
    cards = data["data"]

    for card in cards:
        cursor.execute("""
        INSERT OR IGNORE INTO cards (id, type, archetype, attribute, atk, def, level)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            card.get("id"),
            card.get("type"),
            card.get("archetype"),
            card.get("attribute"),
            card.get("atk"),
            card.get("def"),
            card.get("level")
            )
        )

        cursor.execute("""
        INSERT OR IGNORE INTO cards_translation (card_id, language, name, description)
        VALUES (?, ?, ?, ?)
        """, (
            card.get("id"),
            language,
            card.get("name"),
            card.get("desc")
        ))

    conn.commit()
    conn.close()

def search_cards(name=None, language="en"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        SELECT cards.id, cards_translation.name
        FROM cards
        JOIN cards_translation
        ON cards.id = cards_translation.card_id
        WHERE cards_translation.language = ?
    """
    params = [language]

    #When we're searching cards on the CardsFrame, the results are filtered with the current typed letters on the
    #searchbox

    if name:
        query += " AND LOWER(cards_translation.name) LIKE LOWER(?)"
        params.append(f"%{name}%")

    query += " ORDER BY cards_translation.name COLLATE NOCASE"

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    return results

def populate_duelists():
    conn = get_connection()
    cursor = conn.cursor()

    #TODO: Use descriptions on DuelistDetailsFrame or remove it.

    duelists = [
        ("Yugi Muto", "King of Games", "images/duelists/yugi.png"),
        ("Seto Kaiba", "CEO, KaibaCorp", "images/duelists/kaiba.png"),
        ("Joey Wheeler", "Brooklyn Duelist", "images/duelists/joey.png")
    ]

    for duelist in duelists:
        cursor.execute("""
        INSERT OR IGNORE INTO duelists (name, description, img_path) 
        VALUES (?, ?, ?)
        """, duelist)

    conn.commit()
    conn.close()

def get_all_duelists():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, name, description, img_path
    FROM duelists
    """)

    results = cursor.fetchall()
    conn.close()
    return results

def populate_decks_and_cards(base_language_for_lookup="en"):
    conn = get_connection()
    cursor = conn.cursor()

    for duelist_name, decks_by_name in DECKS_DATA.items():
        cursor.execute("SELECT id FROM duelists WHERE name = ?", (duelist_name,))
        duelist = cursor.fetchone()
        if not duelist:
            continue
        duelist_id = duelist[0]

        for order_index, (deck_name, cards) in enumerate(decks_by_name.items()):
            deck_type_id = None

            if deck_name in ARC_NAMES: #Deck is from an Arc, like Battle City? Use this to allow translation!
                cursor.execute("""
                    INSERT OR IGNORE INTO deck_types (name, key, order_index)
                    VALUES (?, ?, ?)
                """, (deck_name, deck_name, order_index))

                cursor.execute("SELECT id FROM deck_types WHERE key = ?", (deck_name,))
                row = cursor.fetchone()
                deck_type_id = row[0] if row else None

            cursor.execute("""
                INSERT OR IGNORE INTO decks (duelist_id, deck_type_id, name, order_index)
                VALUES (?, ?, ?, ?)
            """, (duelist_id, deck_type_id, deck_name, order_index))

            cursor.execute("""
                SELECT id
                FROM decks
                WHERE duelist_id = ? AND name = ?
            """, (duelist_id, deck_name))
            deck_id = cursor.fetchone()[0]

            for card_name, quantity in cards:
                cursor.execute("""
                    SELECT card_id
                    FROM cards_translation
                    WHERE name = ? AND language = ?
                    LIMIT 1
                """, (card_name, base_language_for_lookup))
                row = cursor.fetchone()

                if not row:
                    # Fallback. Check TODO in main.py
                    cursor.execute("""
                        SELECT card_id
                        FROM cards_translation
                        WHERE name = ?
                        LIMIT 1
                    """, (card_name,))
                    row = cursor.fetchone()

                if row:
                    card_id = row[0]
                    cursor.execute("""
                        INSERT OR IGNORE INTO deck_cards (deck_id, card_id, quantity)
                        VALUES (?, ?, ?)
                    """, (deck_id, card_id, quantity))
                else:
                    #Didn't find the card? Most likely it's an anime deck, which doesn't have an ID on the API.
                    #We insert its name then.
                    cursor.execute("""
                        INSERT OR IGNORE INTO deck_cards (deck_id, card_name, quantity)
                        VALUES (?, ?, ?)
                    """, (deck_id, card_name, quantity))

    conn.commit()
    conn.close()

def populate_deck_type_translations():
    conn = get_connection()
    cursor = conn.cursor()

    #TODO: When more arcs are created, also modify here. Meanwhile, we're doing Portuguese only.

    translations = [
        ("Toei - First Series", "pt", "Toei - Primeira Série"),
        ("Toei - Death-T", "pt", "Toei - Death-T"),
        ("Toei - Movie", "pt", "Toei - Filme"),
        ("Duelist Kingdom", "pt", "Reino dos Duelistas"),
    ]

    for deck_type_name_en, language, translated_name in translations:
        cursor.execute(
            "SELECT id FROM deck_types WHERE name = ?",
            (deck_type_name_en,)
        )
        row = cursor.fetchone()
        if not row:
            continue

        deck_type_id = row[0]

        cursor.execute("""
            INSERT OR IGNORE INTO deck_type_translation (deck_type_id, language, name)
            VALUES (?, ?, ?)
        """, (deck_type_id, language, translated_name))

    conn.commit()
    conn.close()

def get_decks_by_duelist(duelist_id, language="en", show_anime=True):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            d.id AS deck_id,
            COALESCE(dttr.name, dtr.name, d.name) AS deck_name,
            d.order_index
        FROM decks d
        LEFT JOIN decks_translation dtr
            ON dtr.deck_id = d.id
            AND dtr.language = ?
        LEFT JOIN deck_types dt
            ON dt.id = d.deck_type_id
        LEFT JOIN deck_type_translation dttr
            ON dttr.deck_type_id = dt.id
            AND dttr.language = ?
        WHERE d.duelist_id = ?
        ORDER BY d.order_index
    """, (language, language, duelist_id))

    decks = cursor.fetchall()
    result = []

    for deck_id, deck_name, _order_index in decks:
        parts = ["""
            SELECT
                dc.card_id,
                COALESCE(ct.name, dc.card_name) AS card_name,
                c.atk,
                c.def,
                dc.quantity
            FROM deck_cards dc
            LEFT JOIN cards c
                ON c.id = dc.card_id
            LEFT JOIN cards_translation ct
                ON ct.card_id = c.id
                AND ct.language = ?
            WHERE dc.deck_id = ?
        """]

        #This is a checkbox controlled in DuelistDetailsFrame

        if not show_anime:
            parts.append("AND dc.card_id IS NOT NULL")

        #Alphabetical Order. Could order by Type, like Monster first and Magic/Trap later like the Wiki, but no reason why as of now.
        parts.append("ORDER BY card_name COLLATE NOCASE")
        cards_query = "\n".join(parts)

        cursor.execute(cards_query, (language, deck_id))
        cards = cursor.fetchall()

        result.append({
            "deck_id": deck_id,
            "deck_name": deck_name,
            "cards": cards
        })

    conn.close()
    return result
