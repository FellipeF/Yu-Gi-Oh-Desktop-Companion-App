"""File to populate duelists table"""

from database.database import get_connection
from data.duelists import DUELISTS

def _upsert_duelists(cursor, duelist_rows: list[tuple[str, str | None]]) -> None:
    """Insert in database Duelists that are contained in the duelists.py file located in the data folder. ON CONFLICT
    DO UPDATE is here if I decide to change any of their portraits at some point."""
    if not duelist_rows:
        return

    cursor.executemany("""
    INSERT INTO duelists (key, name, img_path)
    VALUES (?, ?, ?)
    ON CONFLICT (key) DO UPDATE SET
        name = excluded.name,
        img_path = excluded.img_path
    """, duelist_rows, )

def populate_duelists() -> None:
    """Populate duelists Table"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        _upsert_duelists(cursor, DUELISTS)
        conn.commit()
    finally:
        conn.close()