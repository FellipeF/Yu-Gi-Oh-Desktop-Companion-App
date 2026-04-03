import sqlite3

DB_NAME = "yugi.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    # ----------------------------------------------------------------------------------------------------
    # Enable Foreign Keys:
    # https://stackoverflow.com/questions/6288871/foreign-key-support-in-sqlite3?answertab=oldest#tab-top
    # ----------------------------------------------------------------------------------------------------
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA cache_size = -10000")  # ~10 MB
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
        key TEXT UNIQUE NOT NULL,
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
    # this table on seed_decks.py for a consistent approach on deck order when switching duelists. The order in which
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
        FOREIGN KEY (duelist_id) REFERENCES duelists(id) ON DELETE CASCADE,
        FOREIGN KEY (deck_category_id) REFERENCES deck_categories(id) ON DELETE SET NULL,
        UNIQUE(duelist_id, key)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS duelist_deck_translations (
        deck_id INTEGER NOT NULL,
        language_code TEXT NOT NULL,
        name TEXT NOT NULL,
        PRIMARY KEY (deck_id, language_code),
        FOREIGN KEY (deck_id) REFERENCES duelist_decks(id) ON DELETE CASCADE
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
        FOREIGN KEY(deck_id) REFERENCES duelist_decks(id) ON DELETE CASCADE,
        FOREIGN KEY(card_id) REFERENCES cards(id),
        UNIQUE(deck_id, card_id),
        UNIQUE(deck_id, card_name)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_decks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        is_used INTEGER NOT NULL DEFAULT 0
        )
        """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_deck_contents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deck_id INTEGER NOT NULL,
        card_id INTEGER,
        card_name TEXT,
        quantity INTEGER NOT NULL,
        FOREIGN KEY(deck_id) REFERENCES user_decks(id) ON DELETE CASCADE,
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

    # Index for all the decks of a particular duelist
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_duelist_decks_duelist_id_order
    ON duelist_decks(duelist_id, order_index)
    """)

    # Searching translation by language
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_duelist_deck_translations_deck_lang
    ON duelist_deck_translations(deck_id, language_code)
    """)

    # Searching translated category by language
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_deck_category_translations_category_lang
    ON deck_category_translations(deck_category_id, language_code)
    """)

    # Load Duelist deck contents
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_deck_contents_deck_id
    ON deck_contents(deck_id)
    """)

    # Load User Deck Contents
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_user_deck_contents_deck_id
    ON user_deck_contents(deck_id)
    """)

    conn.commit()
    conn.close()

def _foreign_key_matches(
        cursor, table_name: str, from_column: str, referenced_table:str, referenced_column: str, on_delete: str,
) -> bool:
    """Does a specific FK exists with the ON DELETE behavior?"""
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    rows = cursor.fetchall()

    for row in rows:
        _id, _seq, ref_table, from_col, to_col, _on_update, on_delete_rule, _match = row

        if (
            ref_table == referenced_table and
            from_col == from_column
            and to_col == referenced_column
            and on_delete_rule.upper() == on_delete.upper()
        ):
            return True

        return False

def _recreate_duelist_decks_table(cursor):
    """Recreates duelist decks table with correct FK ON DELETE CASCADE Constraint for duelist_id. Then, copies contents
    from old table to this new one, drop the old table and rename the new table to be the same name as the old table."""
    cursor.execute("""
        CREATE TABLE duelist_decks_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            duelist_id INTEGER NOT NULL,
            deck_category_id INTEGER,
            key TEXT NOT NULL,
            order_index INTEGER DEFAULT 0,
            FOREIGN KEY (duelist_id) REFERENCES duelists(id) ON DELETE CASCADE,
            FOREIGN KEY (deck_category_id) REFERENCES deck_categories(id) ON DELETE SET NULL,
            UNIQUE(duelist_id, key)
        )
        """)

    cursor.execute("""
        INSERT INTO duelist_decks_new (id, duelist_id, deck_category_id, key, order_index)
        SELECT id, duelist_id, deck_category_id, key, order_index
        FROM duelist_decks
        """)

    cursor.execute("DROP TABLE duelist_decks")
    cursor.execute("ALTER TABLE duelist_decks_new RENAME TO duelist_decks")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_duelist_decks_duelist_id_order
        ON duelist_decks(duelist_id, order_index)
        """)

def run_migrations():
    """Run migrations on DB only if needed"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        needs_duelist_decks_migration = not _foreign_key_matches(
            cursor,
            table_name="duelist_decks",
            from_column="duelist_id",
            referenced_table="duelists",
            referenced_column="id",
            on_delete="CASCADE",
        )
        if not needs_duelist_decks_migration:
            return

        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("BEGIN")

        try:
            _recreate_duelist_decks_table(cursor)
            cursor.execute("COMMIT")
        except Exception:
            cursor.execute("ROLLBACK")
            raise
        finally:
            cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("PRAGMA foreign_key_check")
        fk_issues = cursor.fetchall()
        if fk_issues:
            raise RuntimeError(f"FK check failed after migration: {fk_issues}")

        conn.commit()
    finally:
        conn.close()