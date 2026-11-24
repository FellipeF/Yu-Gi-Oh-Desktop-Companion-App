from database.database import get_connection


def get_decks_by_duelist(duelist_id: int, language_code: str = "en", show_exclusive_cards: bool = True) -> list[dict]:
    """Returns all decks and their contents for a given duelist. Implements fallback for english if card has no
    translation in the dataset (not yet updated or not found, such as exclusive cards not present in the TCG)"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
            SELECT
                dd.id AS deck_id,
                dd.key AS deck_key,
                COALESCE(
                    dct_lang.name,
                    dct_en.name,
                    ddt_lang.name,
                    ddt_en.name,
                    dd.key
                ) AS deck_name,
                dd.order_index AS deck_order,
                dd.cover_card_id,
                dc.card_id,
                COALESCE(ct_lang.name, ct_en.name, dc.card_name) AS card_name,
                dc.quantity,
                c.type AS card_type
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
            LEFT JOIN cards c
                ON c.id = dc.card_id
            LEFT JOIN cards_translations ct_lang
                ON ct_lang.card_id = c.id
                AND ct_lang.language_code = :lang
            LEFT JOIN cards_translations ct_en
                ON ct_en.card_id = c.id
                AND ct_en.language_code = 'en'
            WHERE dd.duelist_id = :duelist_id
        """

    # checkbox filter, controlled by Duelist Details Frame
    if not show_exclusive_cards:
        query += " AND dc.card_id IS NOT NULL\n"

    query += """
            ORDER BY
                dd.order_index,

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
                        AND c.type NOT LIKE '%Ritual%'
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

                    WHEN dc.card_id IS NULL THEN 6

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

                card_name COLLATE NOCASE
        """

    try:
        cursor.execute(query, {"lang": language_code, "duelist_id": duelist_id})
        rows = cursor.fetchall()
    finally:
        conn.close()

    decks: list[dict] = []
    by_deck: dict[int, dict] = {}

    for deck_id, deck_key, deck_name, _deck_order, cover_card_id, card_id, card_name, qty, card_type in rows:
        if deck_id not in by_deck:
            deck_obj = {
                "deck_id": deck_id,
                "deck_key": deck_key,
                "deck_name": deck_name,
                "cover_card_id": cover_card_id,
                "cards": []
            }
            by_deck[deck_id] = deck_obj
            decks.append(deck_obj)

        # Doesn't hurt to check, leaving this here for future-proof
        if qty is not None:
            by_deck[deck_id]["cards"].append((card_id, card_name, qty, card_type))

    return decks