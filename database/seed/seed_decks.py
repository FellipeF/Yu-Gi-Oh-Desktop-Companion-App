"""File to populate deck categories, duelist decks and the deck contents Tables"""

from database.database import get_connection
from data.duel_monsters.decks import LIST_OF_DECKS_DUEL_MONSTERS
from data.duel_monsters.deck_categories_duel_monsters import DECK_CATEGORIES_KEYS_DUEL_MONSTERS
from data.gx.decks import LIST_OF_DECKS_GX
from data.gx.deck_categories_gx import DECK_CATEGORIES_KEYS_GX
from data.duel_monsters.duel_monsters_decks_cover_cards import DUEL_MONSTERS_DECK_COVER_CARDS
from data.gx.gx_decks_cover_cards import GX_DECK_COVER_CARDS

DecksByDuelist = dict[str, dict[str, list[tuple[str, int]]]]

DECK_COVER_CARDS_BY_ANIME = {
    **DUEL_MONSTERS_DECK_COVER_CARDS,
    **GX_DECK_COVER_CARDS,
} # Dictionary unpacking to gather all of them in one.

SEED_DECK_SOURCES: list[tuple[DecksByDuelist, list[str]]] = [
    (LIST_OF_DECKS_DUEL_MONSTERS, DECK_CATEGORIES_KEYS_DUEL_MONSTERS),
    (LIST_OF_DECKS_GX, DECK_CATEGORIES_KEYS_GX)
]

def _load_duelist_ids(cursor) -> dict[str, int]:
    """Returns a mapping of duelist key to database id"""
    cursor.execute("SELECT id, key FROM duelists")
    return {
        key: duelist_id for duelist_id, key in cursor.fetchall()
    }

def _load_deck_category_ids (cursor) -> dict[str, int]:
    """Returns a mapping of deck category key to database id"""
    cursor.execute("SELECT id, key FROM deck_categories")
    return {
        key: category_id for category_id, key in cursor.fetchall()
    }

def _load_duelist_deck_ids(cursor) -> dict[tuple[int, str],int]:
    """Returns mapping of what duelist ID is mapped to what deck"""
    cursor.execute("SELECT id, duelist_id, key FROM duelist_decks")
    return {
        (duelist_id, deck_key): deck_id for deck_id, duelist_id, deck_key in cursor.fetchall()
    }

def _insert_missing_deck_categories(
        cursor,
        existing_category_ids: dict[str, int],
        deck_category_keys: list[str],
) -> None:
    """Creates deck_categories that currently don't exist. Then, update the dictionary with new ids"""
    rows = [(key, ) for key in deck_category_keys if key not in existing_category_ids]

    if not rows:
        return

    cursor.executemany("""
    INSERT INTO deck_categories (key)
    VALUES (?)
    ON CONFLICT (key) DO NOTHING
    """, rows, )

    cursor.execute("SELECT id, key FROM deck_categories")
    existing_category_ids.clear()
    existing_category_ids.update(
        {
            key: category_id for category_id, key in cursor.fetchall()
        }
    )

def _build_duelist_decks_rows(
        duelist_id_by_key: dict[str, int],
        deck_category_id_by_key: dict[str, int],
        decks_source: DecksByDuelist,
) -> list[tuple[int, int | None, str, int, int | None]]:
    """Prepare rows to UPSERT. As seen in the database model, deck_category_id is populated if this is a shared
    category key"""

    rows: list[tuple[int, int | None, str, int, int | None]] = []

    for duelist_key, decks_by_key in decks_source.items():
        duelist_id = duelist_id_by_key.get(duelist_key)
        if duelist_id is None:
            continue

        for order_index, deck_key in enumerate(decks_by_key.keys()):
            deck_category_id = deck_category_id_by_key.get(deck_key)
            cover_card_id = DECK_COVER_CARDS_BY_ANIME.get(duelist_key, {}).get(deck_key)
            rows.append((duelist_id, deck_category_id, deck_key, order_index, cover_card_id))

    return rows

def _upsert_duelist_decks(
    cursor,
    deck_rows: list[tuple[int, int | None, str, int, int | None]],
) -> None:
    """Insert or update duelist_decks Table"""
    if not deck_rows:
        return

    cursor.executemany("""
    INSERT INTO duelist_decks (duelist_id, deck_category_id, key, order_index, cover_card_id)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT (duelist_id, key) DO UPDATE SET
        deck_category_id = excluded.deck_category_id,
        order_index = excluded.order_index,
        cover_card_id = excluded.cover_card_id
        """, deck_rows, )

def _delete_removed_duelist_decks(cursor, duelist_id_by_key: dict[str, int], decks_source: DecksByDuelist,) -> None:
    """Deletes deck that no longer exist if LIST_OF_DECKS ever change"""
    for duelist_key, decks_by_key in decks_source.items():
        duelist_id = duelist_id_by_key.get(duelist_key)
        if duelist_id is None:
            continue

        expected_deck_keys = list(decks_by_key.keys())

        if expected_deck_keys:
            placeholders = ",".join("?" * len(expected_deck_keys))
            cursor.execute(f"""
            DELETE FROM duelist_decks
            WHERE duelist_id = ?
                AND key NOT IN ({placeholders})
            """, [duelist_id, *expected_deck_keys])
        else:
            cursor.execute("""
            DELETE FROM duelist_decks
            WHERE duelist_id = ?
            """, (duelist_id, ))

def _find_card_ids_by_name(cursor, card_names: list[str], base_language_code_for_lookup: str, ) -> dict[str, int]:
    """Map card names to their IDs. If an ID is known, that means it's a TCG Card and has an image and details to be
    shown to the user. Else, it's a Game/Novel/Anime/Manga/Movie Exclusive Card. If a name is not found at first,
    fallback to other language to cover for missing translations."""
    if not card_names:
        return {}

    card_id_by_name: dict[str, int] = {}

    placeholders = ",".join(["?"] * len(card_names))
    cursor.execute(f"""
    SELECT name, card_id
    FROM cards_translations
    WHERE language_code = ?
        AND name COLLATE NOCASE IN ({placeholders})
    """, [base_language_code_for_lookup, *card_names], )

    for name, card_id in cursor.fetchall():
        card_id_by_name[name.lower()] = card_id

    missing_names = [
        name for name in card_names if name.lower() not in card_id_by_name
    ]

    if not missing_names:
        return card_id_by_name

    fallback_placeholders = ",".join(["?"] * len(missing_names))
    cursor.execute(f"""
    SELECT name, card_id
    FROM cards_translations
    WHERE name COLLATE NOCASE IN ({fallback_placeholders})
    """, missing_names, )

    for name, card_id in cursor.fetchall():
        card_id_by_name.setdefault(name.lower(), card_id)

    return card_id_by_name

def _collect_all_card_names(deck_sources: list[DecksByDuelist],) -> list[str]:
    """Collect unique card names from all seeded decks"""
    all_card_names: set[str] = set()

    for decks_source in deck_sources:
        for decks_by_key in decks_source.values():
            for cards in decks_by_key.values():
                for card_name, _quantity in cards:
                    all_card_names.add(card_name)

    return list(all_card_names)

def _build_deck_content_rows(
        duelist_id_by_key: dict[str, int],
        deck_id_by_duelist_and_key: dict[tuple[int, str], int],
        card_id_by_name: dict [str, int],
        decks_source: DecksByDuelist,
) -> tuple[list[tuple[int, int, int]], list[tuple[int, str, int]]]:
    """Creates 2 rows for UPSERT: one for TCG Official cards, other for exclusive not found in the dataset"""
    rows_with_id: list[tuple[int, int, int]] = []
    rows_with_name: list[tuple[int, str, int]] = []

    for duelist_key, decks_by_key in decks_source.items():
        duelist_id = duelist_id_by_key.get(duelist_key)
        if duelist_id is None:
            continue

        for deck_key, cards in decks_by_key.items():
            deck_id = deck_id_by_duelist_and_key.get((duelist_id, deck_key))
            if deck_id is None:
                continue

            for card_name, quantity in cards:
                card_id = card_id_by_name.get(card_name.lower())

                if card_id is not None:
                    rows_with_id.append((deck_id, card_id, quantity))
                else:
                    rows_with_name.append((deck_id, card_name, quantity))

    return rows_with_id, rows_with_name

def _upsert_deck_contents(
        cursor,
        rows_with_id: list[tuple[int, int, int]],
        rows_with_name: list[tuple[int, str, int]],
) -> None:
    """Insert or Update deck_contents table"""
    if rows_with_id:
        cursor.executemany("""
        INSERT INTO deck_contents (deck_id, card_id, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT (deck_id, card_id) DO UPDATE SET
            quantity = excluded.quantity
            """, rows_with_id, )

    if rows_with_name:
        cursor.executemany("""
        INSERT INTO deck_contents (deck_id, card_name, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT (deck_id, card_name) DO UPDATE SET
            quantity = excluded.quantity
            """, rows_with_name, )

def _delete_removed_deck_contents(
        cursor,
        duelist_id_by_key: dict[str, int],
        deck_id_by_duelist_and_key: dict[tuple[int, str], int],
        card_id_by_name: dict[str, int],
        decks_source: DecksByDuelist,
) -> None:
    """If card is deleted from deck on the file, delete it from the database as well"""
    for duelist_key, decks_by_key in decks_source.items():
        duelist_id = duelist_id_by_key.get(duelist_key)
        if duelist_id is None:
            continue

        for deck_key, cards in decks_by_key.items():
            deck_id = deck_id_by_duelist_and_key.get((duelist_id, deck_key))
            if deck_id is None:
                continue

            expected_card_ids: set[int] = set()
            expected_card_names: set[str] = set()

            for card_name, _quantity in cards:
                card_id = card_id_by_name.get(card_name.lower())
                if card_id is not None:
                    expected_card_ids.add(card_id)
                else:
                    expected_card_names.add(card_name)

            cursor.execute("""
            SELECT id, card_id, card_name
            FROM deck_contents
            WHERE deck_id = ?
            """, (deck_id, ))

            rows_to_delete: list[int] = []

            for row_id, card_id, card_name in cursor.fetchall():
                if card_id is not None:
                    if card_id not in expected_card_ids:
                        rows_to_delete.append(row_id)
                else:
                    if card_name not in expected_card_names:
                        rows_to_delete.append(row_id)

            if rows_to_delete:
                placeholders = ",".join("?" * len(rows_to_delete))
                cursor.execute(f"""
                DELETE FROM deck_contents
                WHERE id IN ({placeholders})
                """, rows_to_delete)

def populate_decks(base_language_code_for_lookup: str = "en") -> None:
    """Populate duelist_decks, deck_categories and deck contents Tables"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        duelist_id_by_key = _load_duelist_ids(cursor)
        deck_category_id_by_key = _load_deck_category_ids(cursor)

        all_deck_sources = [decks_source for decks_source, _ in SEED_DECK_SOURCES]

        for _decks_source, deck_category_keys in SEED_DECK_SOURCES:
            _insert_missing_deck_categories(cursor, deck_category_id_by_key, deck_category_keys)

        all_deck_rows: list[tuple[int, int | None, str, int, int | None]] = []

        for decks_source, _deck_category_keys in SEED_DECK_SOURCES:
            all_deck_rows.extend(_build_duelist_decks_rows(duelist_id_by_key, deck_category_id_by_key, decks_source,))

        _upsert_duelist_decks(cursor, all_deck_rows)

        for decks_source, _deck_category_keys in SEED_DECK_SOURCES:
            _delete_removed_duelist_decks(cursor, duelist_id_by_key,decks_source)

        deck_id_by_duelist_and_key = _load_duelist_deck_ids(cursor)

        all_card_names = _collect_all_card_names(all_deck_sources)
        card_id_by_name = _find_card_ids_by_name(cursor, all_card_names, base_language_code_for_lookup, )

        all_rows_with_id: list[tuple[int, int, int]] = []
        all_rows_with_name: list[tuple[int, str, int]] = []

        for decks_source, _deck_category_keys in SEED_DECK_SOURCES:
            rows_with_id, rows_with_name = _build_deck_content_rows(
                duelist_id_by_key,
                deck_id_by_duelist_and_key,
                card_id_by_name,
                decks_source,
            )

            all_rows_with_id.extend(rows_with_id)
            all_rows_with_name.extend(rows_with_name)

        _upsert_deck_contents(cursor, all_rows_with_id, all_rows_with_name)

        for decks_source, _deck_category_keys in SEED_DECK_SOURCES:
            _delete_removed_deck_contents(
                cursor,
                duelist_id_by_key,
                deck_id_by_duelist_and_key,
                card_id_by_name,
                decks_source,
            )

        conn.commit()
    finally:
        conn.close()
