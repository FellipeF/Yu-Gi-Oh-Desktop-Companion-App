from database.database import get_connection

"""Retrieves information whether the database schema or the dataset has been changed. If so, Drop the old values
and insert the new ones while preserving user-populated tables, like User Decks. During testing of the app, it was
noticed that oddly some cards IDs were changed on the dataset, so this should handle this issue so that duplicates
are not created"""

def get_metadata_value(key: str) -> str | None:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT value
        FROM app_metadata
        WHERE key = ?
        LIMIT 1
        """, (key, ))

        row = cursor.fetchone()
        return row[0] if row else None

    finally:
        conn.close()

def set_metadata_value(key: str, value: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO app_metadata (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value
        """, (key, value))

        conn.commit()

    finally:
        conn.close()

def set_latest_db_change(latest_db_change: str) -> None:
    set_metadata_value("latest_db_change", latest_db_change)

def get_latest_db_change() -> str | None:
    return get_metadata_value("latest_db_change")

def is_db_the_same(latest_db_change: str) -> bool:
    return get_latest_db_change() == latest_db_change

def set_latest_dataset_seeded(dataset_version: str) -> None:
    set_metadata_value("latest_dataset_seeded", dataset_version)

def get_latest_dataset_seeded() -> str | None:
    return get_metadata_value("latest_dataset_seeded")

def is_dataset_the_same(current_dataset_version: str | None) -> bool:
    if not current_dataset_version:
        return True

    return get_latest_dataset_seeded() == current_dataset_version
