from database.database import get_connection
from config import LATEST_DB_CHANGE

"""Controls and retrieve if database SCHEMA has changed, like adding a constraint or adding/removing columns for
hardcoded data only (all Tables except app_metada, user_deck and user_deck_contents). For CONTENT changes,
the seed files already properly deal with UPSERTS"""

def get_latest_db_change() -> str | None:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT value
        FROM app_metadata
        WHERE key = 'latest_db_change'
        LIMIT 1
        """)
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def set_latest_db_change(latest_seed: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO app_metadata (key, value)
        VALUES ('latest_db_change', ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value
            """, (latest_seed, ))
        conn.commit()
    finally:
        conn.close()

def is_db_the_same() -> bool:
    return get_latest_db_change() == LATEST_DB_CHANGE