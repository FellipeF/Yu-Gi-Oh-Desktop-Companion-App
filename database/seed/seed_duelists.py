"""File to populate duelists table"""

from database.database import get_connection
from data.duelists import DUELISTS

def _upsert_duelists(cursor, duelist_rows: list[tuple[str, str | None]]) -> None:
    """Insert in database Duelists that are contained in the duelists.py file located in the data folder. ON CONFLICT
    DO UPDATE is here if I decide to change portraits or name at any point."""
    if not duelist_rows:
        return

    cursor.executemany("""
    INSERT INTO duelists (key, name, img_path)
    VALUES (?, ?, ?)
    ON CONFLICT (key) DO UPDATE SET
        name = excluded.name,
        img_path = excluded.img_path
    """, duelist_rows, )

def _load_existing_duelist_keys(cursor) -> set[str]:
    cursor.execute("SELECT key FROM duelists")
    return {row[0] for row in cursor.fetchall()}

def _delete_missing_duelists(cursor, existing_keys: set[str], seed_keys: set[str]) -> None:
    """Delete duelists from DB when the duelist is removed from the duelist list"""
    keys_to_delete = existing_keys - seed_keys

    if not keys_to_delete:
        return

    placeholders = ",".join(["?"]) * len(keys_to_delete)

    cursor.execute(f"DELETE FROM duelists WHERE key IN ({placeholders})", tuple(keys_to_delete))

def populate_duelists() -> None:
    """Populate duelists Table and check if there are any leftovers"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        existing_keys = _load_existing_duelist_keys(cursor)
        _upsert_duelists(cursor, DUELISTS)
        seed_keys = {key for key, _, _ in DUELISTS}
        _delete_missing_duelists(cursor, existing_keys, seed_keys)
        conn.commit()
    finally:
        conn.close()