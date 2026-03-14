from database.database import get_connection

def search_cards(name: str | None = None, language: str = "en") -> list[tuple]:
    """Search cards, filtered by language. Also implements fallback in case selected language doesn't have a translation
    for the card"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT cards.id, 
            COALESCE (cards_translations_lang.name, cards_translations_en.name) AS resolved_name
        FROM cards
        LEFT JOIN cards_translations AS cards_translations_lang
            ON cards.id = cards_translations_lang.card_id
            AND cards_translations_lang.language_code = ?
        LEFT JOIN cards_translations AS cards_translations_en
            ON cards.id = cards_translations_en.card_id
            AND cards_translations_en.language_code = 'en'
        WHERE COALESCE (cards_translations_lang.name, cards_translations_en.name) IS NOT NULL
    """
    params = [language]

    if name:
        query += " AND COALESCE (cards_translations_lang.name, cards_translations_en.name) LIKE ? COLLATE NOCASE"
        params.append(f"%{name}%")

    query += " ORDER BY COALESCE (cards_translations_lang.name, cards_translations_en.name) COLLATE NOCASE"

    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        conn.close()

def get_all_duelists() -> list[tuple]:
    """Returns all duelists ordered by name"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT id, name, img_path
        FROM duelists
        ORDER BY name COLLATE NOCASE""")

        return cursor.fetchall()
    finally:
        conn.close()

def get_decks_by_duelist(duelist_id: int, language_code: str ="en", show_exclusive_cards: bool =True) -> list[dict]:
    """Returns all decks for a duelist, with translated deck and card names. Implements fallback for english if card
    has no translation in the dataset (not yet updated or not found, such as exclusive cards not present in the TCG)"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
            SELECT
                dd.id AS deck_id,
                COALESCE(
                    dct_lang.name,
                    dct_en.name,
                    ddt_lang.name,
                    ddt_en.name,
                    dd.key
                ) AS deck_name,
                dd.order_index AS deck_order,
                dc.card_id,
                COALESCE(ct_lang.name, ct_en.name, dc.card_name) AS card_name,
                dc.quantity
            FROM duelist_decks dd
            LEFT JOIN deck_categories dcg
                ON dcg.id = dd.deck_category_id
            LEFT JOIN deck_category_translations dct_lang
                ON dct_lang.deck_category_id = dcg.id
                AND dct_lang.language_code = :lang
            LEFT JOIN deck_category_translations dct_en
                ON dct_en.deck_category_id = dcg.id
                AND dct_en.language_code = 'en'
            LEFT JOIN duelist_deck_translations ddt_lang
                ON ddt_lang.deck_id = dd.id
                AND ddt_lang.language_code = :lang
            LEFT JOIN duelist_deck_translations ddt_en
                ON ddt_en.deck_id = dd.id
                AND ddt_en.language_code = 'en'
            LEFT JOIN deck_contents dc
                ON dc.deck_id = dd.id
        """

    # checkbox filter, controlled by Duelist Details Frame
    if not show_exclusive_cards:
        query += " AND dc.card_id IS NOT NULL\n"

    query += """
            LEFT JOIN cards c
                ON c.id = dc.card_id
            LEFT JOIN cards_translations ct_lang
                ON ct_lang.card_id = c.id
                AND ct_lang.language_code = :lang
            LEFT JOIN cards_translations ct_en
                ON ct_en.card_id = c.id
                AND ct_en.language_code = 'en'
            WHERE dd.duelist_id = :duelist_id
            ORDER BY
                dd.order_index,
                card_name COLLATE NOCASE
        """

    try:
        cursor.execute(query, {"lang": language_code, "duelist_id": duelist_id})
        rows = cursor.fetchall()
    finally:
        conn.close()

    decks: list[dict] = []
    by_deck: dict[int, dict] = {}

    for deck_id, deck_name, _deck_order, card_id, card_name, qty in rows:
        if deck_id not in by_deck:
            deck_obj = {
                "deck_id": deck_id,
                "deck_name": deck_name,
                "cards": []
            }
            by_deck[deck_id] = deck_obj
            decks.append(deck_obj)

        #TODO: Take this out after testing, decks should never be empty on the final version.
        if qty is not None:
            by_deck[deck_id]["cards"].append((card_id, card_name, qty))

    return decks

def get_card_details(card_id: int, language_code="en"):
    """When card is selected on DuelistDetailsFrame or CardsFrame, user can verify additional info on the card"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                c.id,
                COALESCE(ct_lang.name, ct_en.name) AS name,
                COALESCE(ct_lang.description, ct_en.description, '') AS description,
                c.atk,
                c.def,
                c.type
            FROM cards c
            LEFT JOIN cards_translations ct_lang
                ON ct_lang.card_id = c.id
                AND ct_lang.language_code = ?
            LEFT JOIN cards_translations ct_en
                ON ct_en.card_id = c.id
                AND ct_en.language_code = 'en'
            WHERE c.id = ?
            LIMIT 1
            """,
            (language_code, card_id),
        )
        return cursor.fetchone()
    finally:
        conn.close()

def get_cards_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM cards")
        return cursor.fetchone()[0]
    finally:
        conn.close()

def get_duelists_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM duelists")
        return cursor.fetchone()[0]
    finally:
        conn.close()

def get_user_decks_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM user_decks")
        return cursor.fetchone()[0]
    finally:
        conn.close()

def get_all_user_decks() -> list[tuple]:
    """Returns a list of all custom decks created or imported by the user"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                ud.id,
                ud.name,
                ud.is_used,
                COALESCE(SUM(udc.quantity), 0) AS total_cards
            FROM user_decks ud
            LEFT JOIN user_deck_contents udc
                ON udc.deck_id = ud.id
            GROUP BY ud.id, ud.name, ud.is_used
            ORDER BY ud.name COLLATE NOCASE
            """
        )
        return cursor.fetchall()
    finally:
        conn.close()

def get_user_deck_by_id(deck_id: int) -> tuple | None:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT id, name, is_used
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
    """
    Returns all cards from a user deck, with translated card names when possible.
    Fallback:
    translated name in selected language -> english translation -> stored card_name

    Output:
        [
            (card_id, resolved_card_name, quantity),
            ...
        ]
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                udc.card_id,
                COALESCE(ct_lang.name, ct_en.name, udc.card_name) AS resolved_card_name,
                udc.quantity
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
            ORDER BY resolved_card_name COLLATE NOCASE
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
    """
    Adds a card to a user deck.

    Rules:
    - Use card_id when the card exists in the API/database.
    - Use card_name when the card is exclusive and has no official ID.
    - If the card already exists in the deck, increase quantity.
    """
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
    """
    Sets the quantity of a card in a user deck.
    If quantity <= 0, removes the card from the deck.
    """
    if card_id is None and not card_name:
        raise ValueError("You must provide either card_id or card_name.")

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
    """
    Removes a card from a user deck.
    """
    if card_id is None and not card_name:
        raise ValueError("You must provide either card_id or card_name.")

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