from database.database import get_connection

def get_user_decks_count() -> int:
    """Counts how many decks user has created or imported"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM user_decks")
        return cursor.fetchone()[0]
    finally:
        conn.close()

def get_all_user_decks() -> list[tuple]:
    """Returns a list of name, sum of total cards, used status for all custom decks created or imported by the user"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                ud.id,
                ud.name,
                ud.is_used,
                COALESCE(SUM(
                    CASE
                        WHEN c.type LIKE '%Fusion%' THEN 0
                        WHEN c.type LIKE '%Synchro%' THEN 0
                        WHEN c.type LIKE '%Xyz%' THEN 0
                        WHEN c.type LIKE '%Link%' THEN 0
                        ELSE udc.quantity
                    END
                ), 0) AS main_count,
                COALESCE(SUM(
                    CASE
                        WHEN c.type LIKE '%Fusion%' THEN udc.quantity
                        WHEN c.type LIKE '%Synchro%' THEN udc.quantity
                        WHEN c.type LIKE '%Xyz%' THEN udc.quantity
                        WHEN c.type LIKE '%Link%' THEN udc.quantity
                        ELSE 0
                    END
                ), 0) AS extra_count
            FROM user_decks ud
            LEFT JOIN user_deck_contents udc
                ON udc.deck_id = ud.id
            LEFT JOIN cards c
                ON c.id = udc.card_id
            GROUP BY ud.id, ud.name, ud.is_used
            ORDER BY ud.name COLLATE NOCASE
            """
        )
        return cursor.fetchall()
    finally:
        conn.close()

def get_user_deck_by_id(deck_id: int) -> tuple | None:
    """Gets ID from the controller and searches for deck with that corresponding id"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT id, name, is_used, notes
        FROM user_decks
        WHERE id = ?
        LIMIT 1
        """, (deck_id, ))
        return cursor.fetchone()
    finally:
        conn.close()

def create_user_deck(name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO user_decks (name)
        VALUES (?)
        """, (name, ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def delete_user_deck(deck_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        DELETE FROM user_decks
        WHERE id = ?
        """, (deck_id, ))
        conn.commit()
    finally:
        conn.close()

def update_user_deck_used_flag(deck_id: int, is_used: bool):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        UPDATE user_decks
        SET is_used = ?
        WHERE id = ?
        """, (1 if is_used else 0, deck_id))
        conn.commit()
    finally:
        conn.close()

def update_user_deck_notes(deck_id: int, notes: str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        UPDATE user_decks
        SET notes = ?
        WHERE id = ?
        """, (notes, deck_id))

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def rename_user_deck(deck_id: int, new_name: str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        UPDATE user_decks
        SET name = ?
        WHERE id = ?
        """, (new_name, deck_id))
        conn.commit()
    finally:
        conn.close()

def get_cards_by_user_deck(deck_id: int, language_code: str = "en") -> list[tuple]:
    """Returns all cards from a user deck, with translated card names when possible. Also implements Fallback for when
    translated name in selected language doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                udc.card_id,
                COALESCE(ct_lang.name, ct_en.name, udc.card_name) AS resolved_card_name,
                udc.quantity,
                c.type AS card_type,
                CASE
                    WHEN c.type LIKE '%Fusion%' THEN 'extra'
                    WHEN c.type LIKE '%Synchro%' THEN 'extra'
                    WHEN c.type LIKE '%xyz%' THEN 'extra'
                    WHEN c.type LIKE '%Link%' THEN 'extra'
                    ELSE 'main'
                END as deck_section
            FROM user_deck_contents udc
            LEFT JOIN cards c
                ON c.id = udc.card_id
            LEFT JOIN cards_translations ct_lang
                ON ct_lang.card_id = c.id
                AND ct_lang.language_code = ?
            LEFT JOIN cards_translations ct_en
                ON ct_en.card_id = c.id
                AND ct_en.language_code = 'en'
            WHERE udc.deck_id = ?
            ORDER BY 
                CASE
                    WHEN c.type LIKE '%Fusion%'
                        OR c.type LIKE '%Synchro%'
                        OR c.type LIKE '%XYZ%'
                        OR c.type LIKE '%Link%'
                    THEN 1
                    ELSE 0
                END,
                    
                CASE
                    WHEN c.type LIKE '%Normal%'
                        AND c.type NOT LIKE '%Pendulum%'
                    THEN 0
                    
                    WHEN c.type LIKE '%Monster%'
                        AND c.type NOT LIKE '%Pendulum%'
                        AND C.type NOT LIKE '%Ritual%'
                        AND c.type NOT LIKE '%Fusion%'
                        AND c.type NOT LIKE '%Synchro%'
                        AND c.type NOT LIKE '%XYZ%'
                        AND c.type NOT LIKE '%Link%'
                    THEN 1
                    
                    WHEN c.type LIKE '%Pendulum%'
                        AND c.type NOT LIKE '%Ritual%'
                        AND c.type NOT LIKE '%Fusion%'
                        AND c.type NOT LIKE '%Synchro%'
                        AND c.type NOT LIKE '%XYZ%'
                    THEN 2
                    
                    WHEN c.type LIKE '%Ritual%' THEN 3
                    
                    WHEN c.type = 'Spell Card' THEN 4
                    
                    WHEN c.type = 'Trap Card' THEN 5
                    
                    WHEN c.type LIKE '%Fusion%'
                        AND c.type NOT LIKE '%Pendulum%'
                    THEN 10
                    
                    WHEN c.type LIKE '%Fusion%'
                        AND c.type LIKE '%Pendulum%'
                    THEN 11
                    
                    WHEN c.type LIKE '%Synchro%'
                        AND c.type NOT LIKE '%Pendulum%'
                    THEN 12
                    
                    WHEN c.type LIKE '%Synchro%'
                        AND c.type LIKE '%Pendulum%'
                    THEN 13
                    
                    WHEN c.type LIKE '%XYZ%'
                        AND c.type NOT LIKE '%Pendulum%'
                    THEN 14
                    
                    WHEN c.type LIKE '%XYZ%'
                        AND c.type LIKE '%Pendulum%'
                    THEN 15
                    
                    WHEN c.type LIKE '%Link%' THEN 16
                    
                    ELSE 99
            END,
            resolved_card_name COLLATE NOCASE
        """, (language_code, deck_id))
        return cursor.fetchall()
    finally:
        conn.close()


def add_card_to_user_deck(
    deck_id: int,
    quantity: int = 1,
    card_id: int | None = None,
    card_name: str | None = None,
) -> bool:
    """Adds selected card to User Deck. If the card already exists, do a +1. Also stops user from adding more than
    3 copies of a card, per Yu-Gi-Oh! Rules"""

    # This won't check for current banlists or limited cards, since it's meant to be an universal app.

    if card_id is None and not card_name:
        raise ValueError("You must provide either card_id or card_name.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if card_id is not None:
            cursor.execute("""
                SELECT id, quantity
                FROM user_deck_contents
                WHERE deck_id = ?
                AND card_id = ?
                LIMIT 1
            """, (deck_id, card_id))

            existing = cursor.fetchone()

            if existing:
                content_id, current_quantity = existing
                new_quantity = current_quantity + quantity

                if new_quantity > 3:
                    return False

                cursor.execute("""
                    UPDATE user_deck_contents
                    SET quantity = ?
                    WHERE id = ?
                """, (new_quantity, content_id))
            else:
                if quantity > 3:
                    return False

                cursor.execute("""
                    INSERT INTO user_deck_contents (deck_id, card_id, card_name, quantity)
                    VALUES (?, ?, NULL, ?)
                """, (deck_id, card_id, quantity))

        else:
            cursor.execute("""
                SELECT id, quantity
                FROM user_deck_contents
                WHERE deck_id = ?
                AND card_name = ?
                LIMIT 1
            """, (deck_id, card_name))

            existing = cursor.fetchone()

            if existing:
                content_id, current_quantity = existing
                new_quantity = current_quantity + quantity

                if new_quantity > 3:
                    return False

                cursor.execute("""
                    UPDATE user_deck_contents
                    SET quantity = ?
                    WHERE id = ?
                """, (new_quantity, content_id))
            else:
                if quantity > 3:
                    return False

                cursor.execute("""
                    INSERT INTO user_deck_contents (deck_id, card_id, card_name, quantity)
                    VALUES (?, NULL, ?, ?)
                """, (deck_id, card_name, quantity))

        conn.commit()
        return True
    finally:
        conn.close()


def update_user_deck_card_quantity(
    deck_id: int,
    quantity: int,
    card_id: int | None = None,
    card_name: str | None = None,
) -> bool:
    """Updates deck card quantity on the user Deck. Removes card if user removes one copy when there is only that one"""

    if quantity > 3:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if quantity <= 0:
            if card_id is not None:
                cursor.execute("""
                    DELETE FROM user_deck_contents
                    WHERE deck_id = ?
                    AND card_id = ?
                """, (deck_id, card_id))
            else:
                cursor.execute("""
                    DELETE FROM user_deck_contents
                    WHERE deck_id = ?
                    AND card_name = ?
                """, (deck_id, card_name))
        else:
            if card_id is not None:
                cursor.execute("""
                    UPDATE user_deck_contents
                    SET quantity = ?
                    WHERE deck_id = ?
                    AND card_id = ?
                """, (quantity, deck_id, card_id))
            else:
                cursor.execute("""
                    UPDATE user_deck_contents
                    SET quantity = ?
                    WHERE deck_id = ?
                    AND card_name = ?
                """, (quantity, deck_id, card_name))

        conn.commit()
        return True
    finally:
        conn.close()


def remove_card_from_user_deck(
    deck_id: int,
    card_id: int | None = None,
    card_name: str | None = None,
):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if card_id is not None:
            cursor.execute("""
                DELETE FROM user_deck_contents
                WHERE deck_id = ?
                AND card_id = ?
            """, (deck_id, card_id))
        else:
            cursor.execute("""
                DELETE FROM user_deck_contents
                WHERE deck_id = ?
                AND card_name = ?
            """, (deck_id, card_name))

        conn.commit()
    finally:
        conn.close()

def add_cards_bulk_import(deck_id, cards):
    """Inserts multiple cards into a deck using a single transaction. Used when importing decks"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        rows = []

        for card in cards:
            card_id = card.get("id")
            card_name = card.get("name")
            quantity = card.get("quantity")

            rows.append((deck_id, card_id, card_name if card_id is None else None, quantity))

        cursor.executemany("""
        INSERT INTO user_deck_contents (deck_id, card_id, card_name, quantity)
        VALUES (?, ?, ?, ?)
        """, rows)

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
