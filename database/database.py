import sqlite3
from config import DB_NAME

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    # ----------------------------------------------------------------------------------------------------
    # Enable Foreign Keys:
    # https://stackoverflow.com/questions/6288871/foreign-key-support-in-sqlite3?answertab=oldest#tab-top
    # ----------------------------------------------------------------------------------------------------
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
    # Type, archetype and attribute fields are not translated on other languages in the API

    # Card ID is defined by Konami themselves, so that's not an Auto Increment

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY,
        type TEXT,
        readablecardtype TEXT,
        archetype TEXT,
        attribute TEXT,
        atk INTEGER,
        def INTEGER,
        level INTEGER,
        race TEXT,
        scale INTEGER,
        linkval INTEGER,
        linkmarkers TEXT
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
        img_path TEXT,
        media TEXT
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

    # Stores metadata so that app can check if there's a new database schema or if dataset has been updated.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
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

# ----------------------------------------------------------------------------------------------------
# Since plenty of data here is hardcoded for now, I'm leaving the "complex" migration inside comments
# and opting for a simple DROP + DELETE, but it was a good practice on standards. Also, could totally reuse
# those when adding an additional column on user_decks, since those are not hardcoded.
# ----------------------------------------------------------------------------------------------------

# For Migrations purposes on ALTER TABLE, check Step 7
# https://www.sqlite.org/lang_altertable.html

#
#
#def _column_exists(cursor, table_name: str, column_name: str) -> bool:
#    """Does a column already exists in the table? Used on migration for the duelist table, for example, where media
#    column was added some time after creation."""
#    cursor.execute(f"PRAGMA table_info({table_name})")
#    columns = cursor.fetchall()
#    return any (column[1] == column_name for column in columns)

# def _foreign_key_matches(
#         cursor, table_name: str, from_column: str, referenced_table:str, referenced_column: str, on_delete: str,
# ) -> bool:
#     """Does a specific FK exists with the ON DELETE behavior?"""
#     cursor.execute(f"PRAGMA foreign_key_list({table_name})")
#     rows = cursor.fetchall()
#
#     for row in rows:
#         _id, _seq, ref_table, from_col, to_col, _on_update, on_delete_rule, _match = row
#
#         if (
#             ref_table == referenced_table and
#             from_col == from_column
#             and to_col == referenced_column
#             and on_delete_rule.upper() == on_delete.upper()
#         ):
#             return True
#
#     return False
#
# def _get_associated_schema_objects(cursor, table_name: str):
#     """Returns CREATE statements for indexes, triggers and views related to a table. (Step 3 of schema change)"""
#     cursor.execute("""
#         SELECT type, name, sql
#         FROM sqlite_schema
#         WHERE tbl_name = ?
#           AND type IN ('index', 'trigger', 'view')
#     """, (table_name,))
#     rows = cursor.fetchall()
#
#     objects = []
#     for obj_type, obj_name, obj_sql in rows:
#         if obj_sql is None:
#             continue
#         if obj_type == "index" and obj_name.startswith("sqlite_autoindex"):
#             continue
#         objects.append((obj_type, obj_name, obj_sql))
#
#     return objects
#
# def _recreate_schema_objects(cursor, schema_objects):
#     """(Step 8 of schema change)"""
#     for _obj_type, _obj_name, obj_sql in schema_objects:
#         cursor.execute(obj_sql)
#
# def _rebuild_table(cursor, table_name: str, create_new_table_query: str, copy_data_query: str):
#     """Rebuilds table following steps 4 - 7 from the docs and then calls step 8"""
#     schema_objects = _get_associated_schema_objects(cursor, table_name)
#
#     cursor.execute(create_new_table_query)
#     cursor.execute(copy_data_query)
#     cursor.execute(f"DROP TABLE {table_name}")
#     cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")
#     _recreate_schema_objects(cursor, schema_objects)
#
# def _migrate_duelists_schema(cursor):
#     """Since an intermediate version of the duelists table with a media column was created but it's not representative
#     of the final version, need to also check that before doing the migration."""
#     has_name = _column_exists(cursor, "duelists", "name")
#     has_media = _column_exists(cursor, "duelists", "media")
#     has_img_path = _column_exists(cursor, "duelists", "img_path")
#
#     schema_is_final = (
#         _column_exists(cursor, "duelists", "key") and
#         has_img_path and
#         has_media and
#         not has_name #Name was dropped in current version.
#     )
#
#     if schema_is_final:
#         return
#
#     # Step 1 and 2
#     cursor.execute("PRAGMA foreign_keys = OFF")
#     cursor.execute("BEGIN")
#
#     try:
#         create_new_table_query = """
#                 CREATE TABLE duelists_new (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     key TEXT UNIQUE NOT NULL,
#                     img_path TEXT,
#                     media TEXT
#                 )
#                 """
#
#         if has_name and has_media:
#             copy_data_query = """
#                 INSERT INTO duelists_new (id, key, img_path, media)
#                 SELECT id, key, img_path, media
#                 FROM duelists
#                 """
#         elif has_name and not has_media:
#             copy_data_query = """
#                 INSERT INTO duelists_new (id, key, img_path, media)
#                 SELECT id, key, img_path, NULL
#                 FROM duelists
#                 """
#         elif not has_name and not has_media:
#             copy_data_query = """
#                 INSERT INTO duelists_new (id, key, img_path, media)
#                 SELECT id, key, img_path, NULL
#                 FROM duelists
#                 """
#         else:
#             copy_data_query = """
#                 INSERT INTO duelists_new (id, key, img_path, media)
#                 SELECT id, key, img_path, media
#                 FROM duelists
#                 """
#
#         _rebuild_table(
#             cursor,
#             table_name="duelists",
#             create_new_table_query=create_new_table_query,
#             copy_data_query=copy_data_query)
#
#         # Step 10
#         cursor.execute("PRAGMA foreign_key_check")
#         fk_issues = cursor.fetchall()
#         if fk_issues:
#             raise RuntimeError(f"FK check failed after migration: {fk_issues}")
#
#         #Step 11
#         cursor.execute("COMMIT")
#     except Exception:
#         cursor.execute("ROLLBACK")
#         raise
#     finally:
#         #Step 12
#         cursor.execute("PRAGMA foreign_keys = ON")
#
# def _migrate_duelist_decks_fk(cursor):
#     """Recreates duelist decks table with correct FK ON DELETE CASCADE Constraint for duelist_id. Then follows the steps
#     according to the docs"""
#     needs_duelist_decks_migration = not _foreign_key_matches(
#         cursor,
#         table_name="duelist_decks",
#         from_column="duelist_id",
#         referenced_table="duelists",
#         referenced_column="id",
#         on_delete="CASCADE",
#     )
#     if not needs_duelist_decks_migration:
#         return
#
#     # Step 1 and 2
#     cursor.execute("PRAGMA foreign_keys = OFF")
#     cursor.execute("BEGIN")
#
#     try:
#         create_new_table_query = """
#                 CREATE TABLE duelist_decks_new (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     duelist_id INTEGER NOT NULL,
#                     deck_category_id INTEGER,
#                     key TEXT NOT NULL,
#                     order_index INTEGER DEFAULT 0,
#                     FOREIGN KEY (duelist_id) REFERENCES duelists(id) ON DELETE CASCADE,
#                     FOREIGN KEY (deck_category_id) REFERENCES deck_categories(id) ON DELETE SET NULL,
#                     UNIQUE(duelist_id, key)
#                 )
#             """
#
#         copy_data_query = """
#                 INSERT INTO duelist_decks_new (id, duelist_id, deck_category_id, key, order_index)
#                 SELECT id, duelist_id, deck_category_id, key, order_index
#                 FROM duelist_decks
#             """
#
#         _rebuild_table(
#             cursor,
#             table_name="duelist_decks",
#             create_new_table_query=create_new_table_query,
#             copy_data_query=copy_data_query)
#
#         # Step 10
#         cursor.execute("PRAGMA foreign_key_check")
#         fk_issues = cursor.fetchall()
#         if fk_issues:
#             raise RuntimeError(f"FK check failed after migration: {fk_issues}")
#
#         # Step 11
#         cursor.execute("COMMIT")
#     except Exception:
#         cursor.execute("ROLLBACK")
#         raise
#     finally:
#         # Step 12
#         cursor.execute("PRAGMA foreign_keys = ON")
#
# def run_migrations():
#     """Run migrations on DB only if needed"""
#     conn = get_connection()
#     cursor = conn.cursor()
#
#     try:
#         _migrate_duelists_schema(cursor)
#         _migrate_duelist_decks_fk(cursor)
#     finally:
#         conn.close()

# ----------------------------------------------------------------------------------------------------
# END
# ----------------------------------------------------------------------------------------------------