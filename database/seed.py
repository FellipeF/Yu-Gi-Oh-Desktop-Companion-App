"""This file populates the database with card data from the YGOPro API and the data folder, where we can find duelists
and their decks."""
from database.database import get_connection
from services.api_client import ApiClient
from data.duelists import DUELISTS
from data.decks import LIST_OF_DECKS
from data.arcs import ARC_NAMES

api = ApiClient()

def _stat(value):
    """Since the API sets atk and def to -1 values for monster that have those stats as ????, like Egyptian Gods,
    we treat those values as None instead"""
    return None if value == -1 else value

def populate_cards(language:str="en"):
    """Inserts or update cards and their translation in the database. If errata is published, the UPSERT guarantees
    that the new data retrieved from the API is inserted on respective table. In case no changes were made, since we check
    if there's an entry on the cards_translation table and if the offline_version is the same as the online one, we don't
    run the UPSERT."""

    #ON CONFLICT DO UPDATE updates the existing row that conflicts with the row proposed for insertion as
    #its alternative action (https://www.postgresql.org/docs/current/sql-insert.html#id-1.9.3.152.6.3.3)

    info = api.read_info_file()
    online_db_version = info.get("database_version") if info else None
    offline_version = info.get("database_offline_version") if info else None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1
        FROM cards_translations
        WHERE language = ?
        LIMIT 1
        """, (language, ))
    language_exists = cursor.fetchone() is not None

    if language_exists and online_db_version and offline_version == online_db_version:
        conn.close()
        return

    data = api.load_cards(language)
    cards = data["data"]

    cards_rows = []
    translations_rows = []

    for card in cards:
        cards_rows.append((
            card.get("id"),
            card.get("type"),
            card.get("archetype"),
            card.get("attribute"),
            _stat(card.get("atk")),
            _stat(card.get("def")),
            card.get("level")
        ))

        translations_rows.append((
            card.get("id"),
            language,
            card.get("name"),
            card.get("desc")
        ))

    # Performance Delta between execute and executemany - https://github.com/oracle/python-oracledb/discussions/300
    cursor.executemany("""
    INSERT INTO cards (id, type, archetype, attribute, atk, def, level)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        type = excluded.type,
        archetype = excluded.archetype,
        attribute = excluded.attribute,
        atk = excluded.atk,
        def = excluded.def,
        level = excluded.level
        """, cards_rows)

    cursor.executemany("""
    INSERT INTO cards_translations (card_id, language, name, description)
    VALUES (?, ?, ?, ?)
    ON CONFLICT (card_id, language) DO UPDATE SET
        name = excluded.name,
        description = excluded.description
        """, translations_rows)

    conn.commit()
    conn.close()
    
    #The offline and online versions are now synced, so update that.
    info = api.read_info_file()
    current_online_db_version = info.get("database_version")
    if current_online_db_version:
        info["database_offline_version"] = current_online_db_version
        api.write_info_file(info)

def populate_duelists():
    """Insert in database Duelists that are contained in the duelists.py file located in the data folder. ON CONFLICT
    DO UPDATE is here if I decide to change any of their portraits at some point."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executemany("""
    INSERT INTO duelists (name, img_path)
    VALUES (?, ?)
    ON CONFLICT (name) DO UPDATE SET
        img_path = excluded.img_path
        """, DUELISTS)

    conn.commit()
    conn.close()


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
            # Per DB model, a deck type is the name of the Arc that is shared among duelists, like Battle City.
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

                    # Search for English first.
                    cursor.execute(
                        f"""
                        SELECT name, card_id
                        FROM cards_translations
                        WHERE language = ?
                          AND name COLLATE NOCASE IN ({placeholders})
                        """,
                        [base_language_for_lookup, *card_names]
                    )
                    for name, card_id in cursor.fetchall():
                        card_id_by_name[
                            name.lower()] = card_id  # Case-insensitive. Fixes issue with dataset inconsistency, like Gamma 'the' Magnet Warrior vs. Gamma The Magnet Warrior

                    # Fallback for cards not translated in dataset.
                    missing = [n for n in card_names if n.lower() not in card_id_by_name]
                    if missing:
                        fallback = ",".join(["?"] * len(missing))
                        cursor.execute(
                            f"""
                            SELECT name, card_id
                            FROM cards_translations
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