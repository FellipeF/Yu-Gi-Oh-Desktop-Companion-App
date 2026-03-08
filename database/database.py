import sqlite3

DB_NAME = "yugi.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    # Enable Foreign Keys -> https://stackoverflow.com/questions/6288871/foreign-key-support-in-sqlite3?answertab=oldest#tab-top
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Cards table stores universal data. Things that are changed on translation are stored in Cards Translation table.
    # Archetype is not translated on other languages in the API
    # Card ID is defined by Konami themselves, so that's not an Auto Increment

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY,
        type TEXT,
        archetype TEXT,
        attribute TEXT,
        atk INTEGER  ,
        def INTEGER,
        level INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cards_translations (
        card_id INTEGER NOT NULL,
        language_code TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY(card_id) REFERENCES cards(id),
        UNIQUE(card_id, language_code)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS duelists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        img_path TEXT
    )
    """)

    # Categories of decks that are shared between multiple duelists, like anime arcs or video games.

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deck_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deck_category_translations (
        deck_category_id INTEGER NOT NULL,
        language_code TEXT NOT NULL,
        name TEXT NOT NULL,
        PRIMARY KEY (deck_category_id, language_code),
        FOREIGN KEY (deck_category_id) REFERENCES deck_categories(id)
    )
    """)

    # Decks that are unique to duelists. Order index is here to be used with enumerate on the seed when we're populating
    # this table on seed.py for a consistent approach on deck order when switching duelists. The order in which
    # decks are populated is defined on each duelist deck file.
    # Since a deck could be part of a category or not, we can configure deck_category_id to be NULL when needed.
    # Example: Kaiba - Battle City. Joey - Battle City. Joey - Super Warrior (Only duelist who has a deck called that)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS duelist_decks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        duelist_id INTEGER NOT NULL,
        deck_category_id INTEGER,
        key TEXT NOT NULL,
        order_index INTEGER DEFAULT 0,
        FOREIGN KEY (duelist_id) REFERENCES duelists(id),
        FOREIGN KEY (deck_category_id) REFERENCES deck_categories(id),
        UNIQUE(duelist_id, key)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS duelist_deck_translations (
        deck_id INTEGER NOT NULL,
        language_code TEXT NOT NULL,
        name TEXT NOT NULL,
        PRIMARY KEY (deck_id, language_code),
        FOREIGN KEY (deck_id) REFERENCES duelist_decks(id)
    )
    """)

    # Shows what cards are part of a given deck. When the card doesn't exist on the API, this means it's an exclusive
    # Manga/Anime/Novel/Game/Movie card, and as such doesn't have an official Konami ID. If that's the case, store
    # its name instead of ID.

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deck_contents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deck_id INTEGER NOT NULL,
        card_id INTEGER,
        card_name TEXT,
        quantity INTEGER NOT NULL,
        FOREIGN KEY(deck_id) REFERENCES duelist_decks(id),
        FOREIGN KEY(card_id) REFERENCES cards(id),
        UNIQUE(deck_id, card_id),
        UNIQUE(deck_id, card_name)
    )
    """)

    # Index for speeding up case-insensitive card name lookups filtered by language_code.
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_cards_translations_lang_name_nocase
    ON cards_translations(language_code, name COLLATE NOCASE)
    """)

    # Speeds up fallback case-insensitive card name lookups across all language_codes
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_cards_translations_name_nocase
    ON cards_translations(name COLLATE NOCASE)
    """)

    conn.commit()
    conn.close()