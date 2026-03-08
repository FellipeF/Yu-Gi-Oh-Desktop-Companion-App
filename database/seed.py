"""This file populates the database with card data from the YGOPro API and the data folder, where we can find duelists
and their decks."""

from data.duelists import DUELISTS
from data.decks import LIST_OF_DECKS
from data.deck_categories import DECK_CATEGORIES_KEYS
from data.deck_categories_translations import DECK_CATEGORIES_TRANSLATIONS

def populate_duelists() -> None:
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

def _load_duelists_ids(cursor) -> dict[str, int]:
    """Loads all duelists in a dictionary, where we can quickly retrieve them by name"""
    cursor.execute("SELECT id, name FROM duelists")
    return {
        name: duelist_id for duelist_id, name in cursor.fetchall()
    }

def _load_deck_category_ids(cursor) -> dict[str, int]:
    """Loads deck_tpes in a dictionary, where we can quickly retrieve them"""
    cursor.execute("SELECT id, key FROM deck_categories")
    return {
        key: category_id for category_id, key in cursor.fetchall()
    }

def _load_duelist_decks_ids(cursor) -> dict[tuple[int, str], int]:
    """Loads decks and associate them to duelists_id"""
    cursor.execute("SELECT id, duelist_id, key FROM duelist_decks")
    return {
        (duelist_id, key): deck_id for deck_id, duelist_id, key in cursor.fetchall()
    }

def _create_missing_deck_categories(cursor, existing_category_ids: dict [str, int]) -> None:
    """Creates deck_types that are not yet populated. Then, update the dictionary with new ids"""
    rows = [(key,) for key in DECK_CATEGORIES_KEYS if key not in existing_category_ids]

    if rows:
        cursor.executemany("""
        INSERT INTO deck_categories (key)
        VALUES (?)
        ON CONFLICT (key) DO NOTHING
        """, rows)
        cursor.execute("SELECT id, key FROM deck_types")
        existing_category_ids.clear()
        existing_category_ids.update(
            {
                key: category_id for category_id, key in cursor.fetchall()
            }
        )

def _create_missing_decks(cursor, deck_rows, deck_id_by_duelist_and_name: dict[tuple[int, str], int]) -> None:
    """Creates decks that are specific to a duelist that are not yet populated. Then, update the dictionary with the
    new ids """
    if not deck_rows:
        return

    cursor.executemany("""
    INSERT INTO decks (duelist_id, deck_type_id, name, order_index)
    VALUES (?, ?, ?, ?)
    ON CONFLICT (duelist_id, name) DO UPDATE SET
        deck_type_id = excluded.deck_type_id,
        order_index = excluded.order_index
        """, deck_rows)

    cursor.execute("SELECT id, duelist_id, name FROM decks")
    deck_id_by_duelist_and_name.clear()
    deck_id_by_duelist_and_name.update (
        {
            (duelist_id, name): deck_id for deck_id, duelist_id, name in cursor.fetchall()
        }
    )

def _find_cards_ids_by_name(cursor, card_names: list[str], base_language_for_lookup: str) -> dict[str, int]:
    """Prepares a dictionary that will map card name with its Konami ID. We search it looking in a base_language, that's
    english for the time being. The name is saved in lowercase so we can search by cards without worrying about
    inconsistencies with typing and wrong capitalization.
    Since some translations still don't exist on the YGOPRO dataset, we need a fallback that searches for the card in
    other language and then add those missing correspondences to the dictionary we created."""
    card_id_by_name: dict[str, int] = {}

    if not card_names:
        return card_id_by_name

    placeholders = ",".join(["?"] * len(card_names))

    cursor.execute(
        f"""SELECT name, card_id
        FROM cards_translations
        WHERE language = ?
        AND name COLLATE NOCASE IN ({placeholders})
        """, [base_language_for_lookup, *card_names]
    )

    for name, card_id in cursor.fetchall():
        card_id_by_name[name.lower()] = card_id

    missing = [name for name in card_names if name.lower() not in card_id_by_name]

    if missing:
        fallback_placeholders = ",".join(["?"] * len(missing))
        cursor.execute(
            f"""SELECT name, card_id
            FROM cards_translations
            WHERE name COLLATE NOCASE IN ({fallback_placeholders})
            """, missing
        )

        for name, card_id in cursor.fetchall():
            card_id_by_name.setdefault(name.lower(), card_id)

    return card_id_by_name


def populate_duelists_decks(base_language_for_lookup="en"):
    """Populate duelists and their decks using dictionaries for better performance. First, we find out what deck_type
    is not added yet and insert into the database. Then, we look at the decks that are specific to duelists and process
    them. Finally, we retrieve cards names and associate them with a duelist deck. If an ID is known, that means it's a
    TCG Card. Else, it's a Game/Novel/Anime/Manga/Movie Exclusive Card"""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        duelist_id_by_name = _load_duelists_ids(cursor)
        deck_type_id_by_key = _load_deck_category_ids(cursor)
        deck_id_by_duelist_and_name = _load_decks_ids(cursor)

        deck_type_rows: list[tuple[str, str, int]] = []
        seen_new_deck_types = set()

        for decks_by_name in LIST_OF_DECKS.values():
            for order_index, deck_name in enumerate(decks_by_name.keys()):
                if deck_name in DECK_CATEGORY_KEYS and deck_name not in deck_type_id_by_key and deck_name not in seen_new_deck_types:
                    deck_type_rows.append((deck_name, deck_name, order_index))
                    seen_new_deck_types.add(deck_name)

        _create_missing_deck_types(cursor, deck_type_rows, deck_type_id_by_key)

        deck_rows: list[tuple[int, int | None, str, int]] = []

        for duelist_name, decks_by_name in LIST_OF_DECKS.items():
            duelist_id = duelist_id_by_name.get(duelist_name)
            if not duelist_id:
                continue

            for order_index, deck_name in enumerate(decks_by_name.keys()):
                deck_type_id = deck_type_id_by_key.get(deck_name) if deck_name in DECK_CATEGORY_KEYS else None
                deck_key = (duelist_id, deck_name)

                if deck_key not in deck_id_by_duelist_and_name:
                    deck_rows.append((duelist_id, deck_type_id, deck_name, order_index))

        _create_missing_decks(cursor, deck_rows, deck_id_by_duelist_and_name)

        all_card_names = set()
        for decks_by_name in LIST_OF_DECKS.values():
            for cards in decks_by_name.values():
                for card_name, _quantity in cards:
                    all_card_names.add(card_name)

        card_id_by_name = _find_cards_ids_by_name(
            cursor,
            list(all_card_names),
            base_language_for_lookup
        )

        rows_with_id: list[tuple[int, int, int]] = []
        rows_with_name: list[tuple[int, str, int]] = []

        for duelist_name, decks_by_name in LIST_OF_DECKS.items():
            duelist_id = duelist_id_by_name.get(duelist_name)
            if not duelist_id:
                continue

            for deck_name, cards in decks_by_name.items():
                deck_id = deck_id_by_duelist_and_name.get((duelist_id, deck_name))
                if not deck_id:
                    continue

                for card_name, quantity in cards:
                    card_id = card_id_by_name.get(card_name.lower())

                    if card_id is not None:
                        rows_with_id.append((deck_id, card_id, quantity))
                    else:
                        rows_with_name.append((deck_id, card_name, quantity))

        if rows_with_id:
            cursor.executemany("""
                INSERT INTO deck_cards (deck_id, card_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT (deck_id, card_id) DO UPDATE SET
                    quantity = excluded.quantity
            """, rows_with_id)

        if rows_with_name:
            cursor.executemany("""
                INSERT INTO deck_cards (deck_id, card_name, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT (deck_id, card_name) DO UPDATE SET
                    quantity = excluded.quantity
            """, rows_with_name)

        conn.commit()

    finally:
        conn.close()

def populate_deck_type_translations():
    """Translate Deck Types, those are anime Arcs, like Battle City, or video games one. Since some of the translations
    are not official, ON CONFLICT assures that those translated names can be changed later if needed."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM deck_types")
    deck_type_id_by_name = {
        name: deck_id for deck_id, name in cursor.fetchall()
    }

    rows = []

    for deck_type_name_en, language, translated_name in DECK_CATEGORIES_TRANSLATIONS:
        deck_type_id = deck_type_id_by_name.get(deck_type_name_en)

        if deck_type_id:
            rows.append((deck_type_id, language, translated_name))

        cursor.executemany("""
            INSERT OR IGNORE INTO deck_type_translation (deck_type_id, language, name)
            VALUES (?, ?, ?)
            ON CONFLICT (deck_type_id, language) DO UPDATE SET
                name = excluded.name
        """, rows)

    conn.commit()
    conn.close()