"""File to populate duelists table"""
from data.duel_spirits.duel_spirits import DUEL_SPIRITS
from database.database import get_connection
from data.duel_monsters_anime.duelists_duel_monsters import DUELISTS_DUEL_MONSTERS
from data.gx.duelists_gx import DUELISTS_GX

# Instead of distinguishing duelists characters and duelist duel monsters on seed, do it here

DuelistSourceRow = tuple[str, str | None, str | None]
DuelistSeedRow = tuple[str, str | None, str | None, str]

SEED_DUELIST_SOURCES: list[tuple[list[DuelistSourceRow], str]] = [
    (DUELISTS_DUEL_MONSTERS, "duelist"),
    (DUELISTS_GX, "duelist"),
    (DUEL_SPIRITS, "duel_monster"),
]

def _upsert_duelists(cursor, duelist_rows: list[DuelistSeedRow]) -> None:
    """Insert in database Duelists that are contained in the duelists files located in each of the data folders."""
    if not duelist_rows:
        return

    cursor.executemany("""
    INSERT INTO duelists (key, img_path, media, duelist_type)
    VALUES (?, ?, ?, ?)
    ON CONFLICT (key) DO UPDATE SET
        img_path = excluded.img_path,
        media = excluded.media,
        duelist_type = excluded.duelist_type
    """, duelist_rows)

def _load_existing_duelist_keys(cursor) -> set[str]:
    cursor.execute("SELECT key FROM duelists")
    return {row[0] for row in cursor.fetchall()}

def _delete_missing_duelists(cursor, existing_keys: set[str], seed_keys: set[str]) -> None:
    """Delete duelists from DB when the duelist is removed from the duelist list"""
    keys_to_delete = existing_keys - seed_keys

    if not keys_to_delete:
        return

    placeholders = ",".join(["?"] * len(keys_to_delete))

    cursor.execute(f"DELETE FROM duelists WHERE key IN ({placeholders})", tuple(keys_to_delete))

def _collect_duelist_rows() -> list[DuelistSeedRow]:
    """Collects duelists from all seed sources"""
    rows: list[DuelistSeedRow] = []

    for duelist_source, duelist_type in SEED_DUELIST_SOURCES:
        for key, img_path, media in duelist_source:
            rows.append((key, img_path, media, duelist_type))

    return rows

def populate_duelists() -> None:
    """Populate duelists Table and check if there are any leftovers"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        duelist_rows = _collect_duelist_rows()
        existing_keys = _load_existing_duelist_keys(cursor)
        _upsert_duelists(cursor, duelist_rows)
        seed_keys = {key for key, _, _, _ in duelist_rows}
        _delete_missing_duelists(cursor, existing_keys, seed_keys)
        conn.commit()
    finally:
        conn.close()