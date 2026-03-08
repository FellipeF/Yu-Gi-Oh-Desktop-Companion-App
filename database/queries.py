from database.database import get_connection

def search_cards(name: str | None = None, language: str = "en") -> list[tuple]:
    """Search cards, filtered by language"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT cards.id, cards_translations.name
        FROM cards
        JOIN cards_translations
        ON cards.id = cards_translations.card_id
        WHERE cards_translations.language_code = ?
    """
    params = [language]

    if name:
        query += " AND cards_translations.name LIKE ? COLLATE NOCASE"
        params.append(f"%{name}%")

    query += " ORDER BY cards_translations.name COLLATE NOCASE"

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