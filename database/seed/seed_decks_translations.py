"""File for populating deck_category and duelist_decks translations tables"""

from database.database import get_connection
from data.deck_categories_translations import DECK_CATEGORIES_TRANSLATIONS
from data.duelists_decks_translations import DUELISTS_DECKS_KEYS

def _load_deck_category_ids(cursor) -> dict[str, int]:
    """Returns mapping of deck category key to database id"""
    cursor.execute("SELECT id, key FROM deck_categories")
    return {
        key: category_id for category_id, key in cursor.fetchall()
    }

def _load_duelist_deck_ids(cursor) -> dict[tuple[str, str], int]:
    """Maps duelist name and key to a duelist_decks.id"""
    cursor.execute("""
    SELECT duelist_decks.id, duelists.key, duelist_decks.key
    FROM duelist_decks
    JOIN duelists ON duelists.id = duelist_decks.duelist_id
    """)

    return {
        (duelist_key, deck_key): deck_id for deck_id, duelist_key, deck_key in cursor.fetchall()
    }

def _build_deck_category_translation_rows(deck_category_id_by_key: dict[str, int], ) -> list[tuple[int, str, str]]:
    """Builds rows for deck category translations to be used on the Upsert"""
    rows: list[tuple[int ,str, str]] = []

    for category_key, translations in DECK_CATEGORIES_TRANSLATIONS.items():
        deck_category_id = deck_category_id_by_key.get(category_key)
        if not deck_category_id:
            continue

        for language_code, translated_name in translations.items():
            rows.append((deck_category_id, language_code, translated_name))

    return rows

def _build_duelist_deck_translation_rows(
        deck_id_by_duelist_and_key: dict[tuple[str, str], int], ) -> list[tuple[int, str, str]]:
    """Builds translation rows for decks that are unique to a duelist"""
    rows: list[tuple[int, str, str]] = []

    for duelist_key, decks in DUELISTS_DECKS_KEYS.items():
        for deck_key, translations in decks.items():
            deck_id = deck_id_by_duelist_and_key.get((duelist_key, deck_key))
            if not deck_id:
                continue

            for language_code, translated_name in translations.items():
                rows.append((deck_id, language_code, translated_name))

    return rows

def _upsert_deck_category_translations(cursor, rows: list[tuple[int, str, str]], ) -> None:
    """Inserts or Update deck_category_translations Table"""
    if not rows:
        return

    cursor.executemany("""
    INSERT INTO deck_category_translations (deck_category_id, language_code, name)
    VALUES (?, ?, ?)
    ON CONFLICT (deck_category_id, language_code) DO UPDATE SET
        name = excluded.name
        """, rows, )

def _upsert_duelist_deck_translations(cursor, rows: list[tuple[int, str, str]], ) -> None:
    """Inserts or Update duelist_decks_translations Table"""
    if not rows:
        return

    cursor.executemany("""
    INSERT INTO duelist_deck_translations (deck_id, language_code, name)
    VALUES (?, ?, ?)
    ON CONFLICT (deck_id, language_code) DO UPDATE SET
        name = excluded.name
        """, rows, )

def populate_deck_category_translations() -> None:
    """Populate deck_category_translations Table"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        deck_category_id_by_key = _load_deck_category_ids(cursor)
        rows = _build_deck_category_translation_rows(deck_category_id_by_key)
        _upsert_deck_category_translations(cursor, rows)
        conn.commit()
    finally:
        conn.close()

def populate_duelist_deck_translations() -> None:
    """Populate duelist_decks_translation Table"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        deck_id_by_duelist_and_key = _load_duelist_deck_ids(cursor)
        rows = _build_duelist_deck_translation_rows(deck_id_by_duelist_and_key)
        _upsert_duelist_deck_translations(cursor, rows)
        conn.commit()
    finally:
        conn.close()