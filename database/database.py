import sqlite3

DB_NAME = "yugi.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # ==========================================================
    # CARDS
    # ==========================================================
    # Archetype is not translated on other languages in the API
    # Card ID is defined by Konami themselves, so that's not an Auto Increment

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY,
        type TEXT,
        archetype TEXT,
        attribute TEXT,
        atk INTEGER,
        def INTEGER,
        level INTEGER
    )
    """)

    #In an universal way, cards_translation also include ENGLISH language, so methods that search card by name
    #actually search this table

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cards_translation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_id INTEGER NOT NULL,
        language TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY(card_id) REFERENCES cards(id),
        UNIQUE(card_id, language)
    )
    """)

    # ==========================================================
    # DUELISTS
    # ==========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS duelists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        img_path TEXT
    )
    """)

    # ==========================================================
    # DECK TYPES (Optional category / Arc). Those are shared across
    # duelists, like Joey Battle City and Kaiba Battle City
    # ==========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deck_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        key TEXT UNIQUE NOT NULL,
        order_index INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deck_type_translation (
        deck_type_id INTEGER NOT NULL,
        language TEXT NOT NULL,
        name TEXT NOT NULL,
        PRIMARY KEY (deck_type_id, language),
        FOREIGN KEY (deck_type_id) REFERENCES deck_types(id)
    )
    """)

    # ==========================================================
    # DECKS (Actual deck instance belonging to a duelist)
    # deck_type_id could be NULL. For example, Yugi has a deck called
    # MAGE POWER. This is not shared across duelists.
    # order_index is here for chronological order reasons
    # ==========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS decks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        duelist_id INTEGER NOT NULL,
        deck_type_id INTEGER,
        name TEXT NOT NULL,
        order_index INTEGER DEFAULT 0,
        FOREIGN KEY (duelist_id) REFERENCES duelists(id),
        FOREIGN KEY (deck_type_id) REFERENCES deck_types(id),
        UNIQUE(duelist_id, name)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS decks_translation (
        deck_id INTEGER NOT NULL,
        language TEXT NOT NULL,
        name TEXT NOT NULL,
        PRIMARY KEY (deck_id, language),
        FOREIGN KEY (deck_id) REFERENCES decks(id)
    )
    """)

    # ==========================================================
    # DECK CARDS
    # card_id = real API card
    # card_name = anime-only or unmatched card
    # ==========================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deck_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deck_id INTEGER NOT NULL,
        card_id INTEGER,
        card_name TEXT,
        quantity INTEGER NOT NULL,
        FOREIGN KEY(deck_id) REFERENCES decks(id),
        FOREIGN KEY(card_id) REFERENCES cards(id),
        UNIQUE(deck_id, card_id),
        UNIQUE(deck_id, card_name)
    )
    """)

    conn.commit()
    conn.close()