import sqlite3
import api_client
from database.database import get_connection
from database.database import DB_NAME
from utils.deck_specific_translation import DECK_SPECIFIC_TRANSLATION
from utils.deck_type_translation import DECK_TYPE_TRANSLATION
from database.decks import LIST_OF_DECKS
from utils.arcs import ARC_NAMES

#TODO: Review db commits and put try except finally blocks
#TODO: Check for performance on other methods

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

    #TODO: Check for cards like Egyptian Gods that ATK and DEF = ???. Currently shows up as -1

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

    #https://www.yugioh.com/characters
    #https://yugioh.fandom.com/wiki/Portal:Yu-Gi-Oh!_anime_characters
    #https://yugioh.fandom.com/wiki/Category:Characters%27_Decks

    duelists = [
        ("Yugi Muto", "images/duelists/yugi.png"),
        ("Seto Kaiba", "images/duelists/kaiba.png"),
        ("Joey Wheeler", "images/duelists/joey.png"),
        ("Yami Yugi", "images/duelists/yami.png"), #TODO
        ("Téa Gardner", "images/duelists/tea.png"),
        ("Tristan Taylor", "images/duelists/tristan.png"),
        ("Solomon Muto", "images/duelists/solomon.png"),
        ("Mokuba Kaiba", "images/duelists/mokuba.png"),
        ("Serenity Wheeler", "images/duelists/serenity.webp"),
        ("Mai Valentine", "images/duelists/mai.png"),
        ("Bakura Ryou", "images/duelists/bakura.webp"),
        ("Yami Bakura", "images/duelists/yami-bakura.png"),
        ("Shadi", "images/duelists/yami-bakura.png"),
        ("Rebecca", "images/duelists/yami-bakura.png"),
        ("Arthur Hopkins", "images/duelists/yami-bakura.png"),
        ("Duke Devlin", "images/duelists/yami-bakura.png"),
        ("Ishizu Ishtar", "images/duelists/yami-bakura.png"),
        ("Pegasus", "images/duelists/yami-bakura.png"),
        ("Weevil", "images/duelists/yami-bakura.png"),
        ("Rex Raptor", "images/duelists/yami-bakura.png"),
        ("Mako Tsunami", "images/duelists/yami-bakura.png"),
        ("Ghost Kaiba", "images/duelists/yami-bakura.png"),
        ("PaniK", "images/duelists/yami-bakura.png"),
        ("Bandit Keith", "images/duelists/yami-bakura.png"),
        ("Bonz", "images/duelists/yami-bakura.png"),
        ("Sid", "images/duelists/yami-bakura.png"),
        ("Zyhor", "images/duelists/yami-bakura.png"),
        ("Para", "images/duelists/yami-bakura.png"),
        ("Dox", "images/duelists/yami-bakura.png"),
        ("Marik Ishtar", "images/duelists/yami-bakura.png"),
        ("Yami Marik", "images/duelists/yami-bakura.png"),
        ("Odion", "images/duelists/yami-bakura.png"),
        ("Seeker", "images/duelists/yami-bakura.png"),
        ("Arkana", "images/duelists/yami-bakura.png"),
        ("Strings", "images/duelists/yami-bakura.png"),
        ("Lumis", "images/duelists/yami-bakura.png"),
        ("Umbra", "images/duelists/yami-bakura.png"),
        ("Noah Kaiba", "images/duelists/yami-bakura.png"),
        ("Gozaburo Kaiba", "images/duelists/yami-bakura.png"),
        ("Gansley", "images/duelists/yami-bakura.png"),
        ("Crump", "images/duelists/yami-bakura.png"),
        ("Johnson", "images/duelists/yami-bakura.png"),
        ("Nezzbitt", "images/duelists/yami-bakura.png"),
        ("Leichter", "images/duelists/yami-bakura.png"),
        ("Dartz", "images/duelists/yami-bakura.png"),
        ("Rafael", "images/duelists/yami-bakura.png"),
        ("Valon", "images/duelists/yami-bakura.png"),
        ("Alister", "images/duelists/yami-bakura.png"),
        ("Gurimo", "images/duelists/yami-bakura.png"),
        ("Orichalcos", "images/duelists/yami-bakura.png"),
        ("Zigfried", "images/duelists/yami-bakura.png"),
        ("Leon", "images/duelists/yami-bakura.png"),
        ("Vivian Wong", "images/duelists/yami-bakura.png"),
        ("Atem", "images/duelists/yami-bakura.png"),
        ("Priest Seto", "images/duelists/yami-bakura.png"),
        ("Mahad", "images/duelists/yami-bakura.png"),
        ("Shimon Muran", "images/duelists/yami-bakura.png"),
        ("Kuriboh", "images/duelists/yami-bakura.png"),
        ("Dark Magician Girl", "images/duelists/yami-bakura.png"),
        ("Red-Eyes B.Dragon", "images/duelists/yami-bakura.png"),
        ("Anubis", "images/duelists/yami-bakura.png"),
        ("Tetsu Trudge", "images/duelists/yami-bakura.png"),
        ("Johnny Steps", "images/duelists/yami-bakura.png"),
        ("Roland", "images/duelists/yami-bakura.png"),
        ("Duel Computer", "images/duelists/yami-bakura.png"),
        ("Espa Roba", "images/duelists/yami-bakura.png"),
        ("Jean-Claude Magnum", "images/duelists/yami-bakura.png"),
        ("Rick", "images/duelists/yami-bakura.png"),
        ("KC DuelTek 760", "images/duelists/yami-bakura.png"),
        #TODO: Capsule Monsters and Beyond
    ]

    for duelist in duelists:
        cursor.execute("""
        INSERT OR IGNORE INTO duelists (name, img_path) 
        VALUES (?, ?)
        """, duelist)

    conn.commit()
    conn.close()

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

def populate_decks_and_cards(base_language_for_lookup="en"):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name FROM duelists")
        duelist_id_by_name = {name: duelist_id for (duelist_id, name) in cursor.fetchall()}

        cursor.execute("SELECT id, key FROM deck_types")
        deck_type_id_by_key = {key: deck_type_id for (deck_type_id, key) in cursor.fetchall()}

        cursor.execute("SELECT id, duelist_id, name FROM decks")
        deck_id_by_duelist_and_name = {(duelist_id, name): deck_id for (deck_id, duelist_id, name) in cursor.fetchall()}

        def get_or_create_deck_type(deck_name: str, order_index: int):
            #Per DB model, a deck type is the name of the Arc that is shared among duelists, like Battle City.
            if deck_name not in ARC_NAMES:
                return None

            key = deck_name
            existing = deck_type_id_by_key.get(key)
            if existing:
                return existing

            cursor.execute(
                "INSERT OR IGNORE INTO deck_types (name, key, order_index) VALUES (?, ?, ?)",
                (deck_name, key, order_index)
            )
            
            cursor.execute("SELECT id FROM deck_types WHERE key = ?", (key,))
            deck_type_id = cursor.fetchone()[0]
            deck_type_id_by_key[key] = deck_type_id
            return deck_type_id

        def get_or_create_deck(duelist_id: int, deck_name: str, deck_type_id, order_index: int):
            key = (duelist_id, deck_name)
            existing = deck_id_by_duelist_and_name.get(key)
            if existing:
                return existing

            cursor.execute(
                """
                INSERT OR IGNORE INTO decks (duelist_id, deck_type_id, name, order_index)
                VALUES (?, ?, ?, ?)
                """,
                (duelist_id, deck_type_id, deck_name, order_index)
            )
            cursor.execute(
                "SELECT id FROM decks WHERE duelist_id = ? AND name = ?",
                (duelist_id, deck_name)
            )
            duelist_id = cursor.fetchone()[0]
            deck_id_by_duelist_and_name[key] = duelist_id
            return duelist_id

        for duelist_name, decks_by_name in LIST_OF_DECKS.items():
            duelist_id = duelist_id_by_name.get(duelist_name)
            if not duelist_id:
                continue

            for order_index, (deck_name, cards) in enumerate(decks_by_name.items()):
                deck_type_id = get_or_create_deck_type(deck_name, order_index)
                deck_id = get_or_create_deck(duelist_id, deck_name, deck_type_id, order_index)

                card_names = [card_name for (card_name, _qty) in cards]
                card_id_by_name = {}
                
                if card_names:
                    placeholders = ",".join(["?"] * len(card_names))
                    
                    #Search for English first.
                    cursor.execute(
                        f"""
                        SELECT name, card_id
                        FROM cards_translation
                        WHERE language = ?
                          AND name COLLATE NOCASE IN ({placeholders})
                        """,
                        [base_language_for_lookup, *card_names]
                    )
                    for name, card_id in cursor.fetchall():
                        card_id_by_name[name.lower()] = card_id # Case-insensitive. Fixes issue with dataset inconsistency, like Gamma 'the' Magnet Warrior vs. Gamma The Magnet Warrior

                    # Fallback for cards not translated in dataset.
                    missing = [n for n in card_names if n.lower() not in card_id_by_name]
                    if missing:
                        fallback = ",".join(["?"] * len(missing))
                        cursor.execute(
                            f"""
                            SELECT name, card_id
                            FROM cards_translation
                            WHERE name COLLATE NOCASE IN ({fallback})
                            """,
                            missing
                        )
                        for name, card_id in cursor.fetchall():
                            card_id_by_name.setdefault(name.lower(), card_id)

                rows_with_id = []
                rows_with_name = []

                for card_name, quantity in cards:
                    card_id = card_id_by_name.get(card_name.lower())
                    if card_id:
                        rows_with_id.append((deck_id, card_id, quantity))
                    else:
                        rows_with_name.append((deck_id, card_name, quantity))

                if rows_with_id:
                    cursor.executemany(
                        """
                        INSERT OR IGNORE INTO deck_cards (deck_id, card_id, quantity)
                        VALUES (?, ?, ?)
                        """,
                        rows_with_id
                    )

                if rows_with_name:
                    cursor.executemany(
                        """
                        INSERT OR IGNORE INTO deck_cards (deck_id, card_name, quantity)
                        VALUES (?, ?, ?)
                        """,
                        rows_with_name
                    )

        conn.commit()

    finally:
        conn.close()

def populate_deck_type_translations():
    """Translate Deck Types, those are anime Arcs, like Battle City, or video games one"""
    conn = get_connection()
    cursor = conn.cursor()

    for deck_type_name_en, language, translated_name in DECK_TYPE_TRANSLATION:
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
            INSERT OR IGNORE INTO decks_translation (deck_id, language, name) 
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
        LEFT JOIN decks_translation dtr_lang
        ON dtr_lang.deck_id = d.id
        AND dtr_lang.language = :lang
        LEFT JOIN decks_translation dtr_en
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
        LEFT JOIN cards_translation ct_lang
        ON ct_lang.card_id = c.id
        AND ct_lang.language = :lang
        LEFT JOIN cards_translation ct_en
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
        LEFT JOIN cards_translation ct_lang
            ON ct_lang.card_id = c.id AND ct_lang.language = ?
        LEFT JOIN cards_translation ct_en
            ON ct_en.card_id = c.id AND ct_en.language = 'en'
        WHERE c.id = ?
        LIMIT 1
    """, (language, card_id))

    row = cursor.fetchone()
    conn.close()
    return row