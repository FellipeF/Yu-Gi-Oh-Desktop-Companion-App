from database.database import get_connection

def get_all_duelists() -> list[tuple]:
    """Returns all duelists and their deck count"""
    conn = get_connection()
    cursor = conn.cursor()

    # For performance issues, better do this than a SELECT COUNT(*) for each duelist on the Frame
    try:
        cursor.execute("""
        SELECT 
            d.id, d.key, d.img_path, d.media, COUNT(dd.id) AS deck_count
        FROM duelists d
        LEFT JOIN duelist_decks dd ON dd.duelist_id = d.id
        WHERE d.duelist_type = 'duelist'
        GROUP BY d.id, d.key, d.img_path, d.media""")

        return cursor.fetchall()
    finally:
        conn.close()

def get_duelists_count() -> int:
    """Counts all duelists present in the database. Shown in Home Page"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM duelists")
        return cursor.fetchone()[0]
    finally:
        conn.close()

def get_all_duel_spirits() -> list[tuple]:
    """Returns all duel monsters that are duelists and their deck count"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT 
            d.id, d.key, d.img_path, d.media, COUNT(dd.id) AS deck_count
        FROM duelists d
        LEFT JOIN duelist_decks dd ON dd.duelist_id = d.id
        WHERE d.duelist_type = 'duel_monster'
        GROUP BY d.id, d.key, d.img_path, d.media""")

        return cursor.fetchall()
    finally:
        conn.close()

def get_duel_spirits_count() -> int:
    """Returns the total number of Duel Spirits registered as duelists. This count is displayed on the Duel Spirits
    portrait on the Duelists Frame instead of showing the total deck count as other duelists."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM duelists
            WHERE duelist_type = 'duel_monster'
        """)

        result = cursor.fetchone()

        return result[0] if result else 0

    finally:
        conn.close()

def get_all_other_duelists() -> list[tuple]:
    """Returns all duelists that have their own category."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT 
            d.id, d.key, d.img_path, d.media, COUNT(dd.id) AS deck_count
        FROM duelists d
        LEFT JOIN duelist_decks dd ON dd.duelist_id = d.id
        WHERE d.duelist_type = 'other_duelist'
        GROUP BY d.id, d.key, d.img_path, d.media""")

        return cursor.fetchall()
    finally:
        conn.close()

def get_other_duelists_count() -> int:
    """Returns other duelists count, shown in the Other Duelists portrait on the Duelists Frame."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM duelists
            WHERE duelist_type = 'other_duelist'
        """)

        result = cursor.fetchone()
        return result[0] if result else 0

    finally:
        conn.close()