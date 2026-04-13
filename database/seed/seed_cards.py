"""File for populating cards and cards_translations table"""

from database.database import get_connection
from services.api_client import ApiClient

api = ApiClient()

def _normalize_stat(value) -> int | None:
    """Since the API sets atk and def to -1 values for monster that have those stats as ????, like Egyptian Gods,
    we treat those values as None instead"""
    return None if value == -1 else value

def _get_database_version(language_code: str) -> tuple[str | None, str | None]:
    """Returns the online dataset version and offline database version from the info file"""
    info = api.read_info_file() or {}
    lang_info = info.get(language_code, {})
    offline_version = lang_info.get("database_offline_version")

    try:
        db_details = api.get_dataset_details()
        online_version = db_details.get("database_version")
    except Exception:
        online_version = lang_info.get("database_version")

    return online_version, offline_version

def _is_language_already_seeded(cursor, language_code: str) -> bool:
    """Check if at least one translation row already exists """
    cursor.execute("""
    SELECT 1
    FROM cards_translations
    WHERE language_code = ?
    LIMIT 1
    """, (language_code, ),
    )
    return cursor.fetchone() is not None

def _should_skip_cards_seed(cursor, language_code: str) -> bool:
    """Check if the selected language is already seeded and if versions match"""
    online_version, offline_version = _get_database_version(language_code)
    language_exists = _is_language_already_seeded(cursor, language_code)

    if not online_version: # If API fails to fetch due to timeout, avoid continuing
        return False

    return bool(language_exists and online_version and offline_version == online_version)

def _build_cards_rows(cards: list[dict], language_code: str) -> tuple[list[tuple], list[tuple]]:
    """Prepare API payload to UPSERT cards and cards_translations Tables"""
    cards_rows: list[tuple] = []
    translations_rows: list[tuple] = []

    for card in cards:
        card_id = card.get("id")

        cards_rows.append(
            (
                card_id,
                card.get("type"),
                card.get("archetype"),
                card.get("attribute"),
                _normalize_stat(card.get("atk")),
                _normalize_stat(card.get("def")),
                card.get("level"),
            )
        )

        translations_rows.append(
            (
                card_id,
                language_code,
                card.get("name"),
                card.get("desc"),
            )
        )

    return cards_rows, translations_rows

def _upsert_cards(cursor, cards_rows: list[tuple]) -> None:
    """Inserts or update cards in the cards Table. If errata is published, the UPSERT guarantees that the new data
    retrieved from the API is inserted on respective table."""
    # ON CONFLICT DO UPDATE updates the existing row that conflicts with the row proposed for insertion as
    # its alternative action (https://www.postgresql.org/docs/current/sql-insert.html#id-1.9.3.152.6.3.3)

    if not cards_rows:
        return

    # Performance Delta between execute and executemany - https://github.com/oracle/python-oracledb/discussions/300
    cursor.executemany("""
    INSERT INTO cards (id, type, archetype, attribute, atk, def, level)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (id) DO UPDATE SET
        type = excluded.type,
        archetype = excluded.archetype,
        attribute = excluded.attribute,
        atk = excluded.atk,
        def = excluded.def,
        level = excluded.level
        """, cards_rows, )

def _upsert_cards_translations(cursor, translation_rows: list[tuple]) -> None:
    """Inserts or update cards in the cards_translation Table. If errata is published, the UPSERT guarantees that the
    new data retrieved from the API is inserted on respective table."""

    if not translation_rows:
        return

    cursor.executemany("""
    INSERT INTO cards_translations (card_id, language_code, name, description)
    VALUES (?, ?, ?, ?)
    ON CONFLICT (card_id, language_code) DO UPDATE SET
        name = excluded.name,
        description = excluded.description
        """, translation_rows,)

def _sync_offline_database_version(language_code: str) -> None:
    """After a successful seed, update info file to update current offline version with current online version"""
    info = api.read_info_file() or {}
    lang_info = info.get(language_code, {})
    current_online_version = lang_info.get("database_version")

    if not current_online_version:
        return

    lang_info["database_offline_version"] = current_online_version
    info[language_code] = lang_info
    api.write_info_file(info)

def populate_cards(language_code: str = "en") -> None:
    """Populate cards and cards_translation Tables with data from the API"""

    conn = get_connection()
    cursor = conn.cursor()

    try:
        payload = api.load_cards(language_code)

        if _should_skip_cards_seed(cursor, language_code):
            return

        cards = payload.get("data", [])
        if not cards:
            raise ValueError(f"No card data returned for language {language_code}") # TODO: Show this to user

        cards_rows, translations_rows = _build_cards_rows(cards, language_code)

        _upsert_cards(cursor, cards_rows)
        _upsert_cards_translations(cursor, translations_rows)

        conn.commit()
    finally:
        conn.close()

    _sync_offline_database_version(language_code)