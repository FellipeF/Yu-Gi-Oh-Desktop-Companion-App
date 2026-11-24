from database.queries import search_cards

class CardSearchService:
    """Controls and cache searched cards on CardsFrame and CustomDeckEditorFrame search boxes. This cache is
    written as a dictionary, where the language_code contains id, original name and the lower-case name so that
    a .lower() doesn't need to be called everytime a letter is typed"""
    def __init__(self):
        self._cards_cache: dict[str, list[tuple[int, str, str]]] = {}

    def _ensure_cache(self, language_code: str) -> None:
        """Initializes the cache for the requested language"""
        if language_code not in self._cards_cache:
            cards = search_cards(language=language_code)

            self._cards_cache[language_code] = [(card_id, name, name.lower()) for card_id, name in cards]

    def get_all_cards(self, language_code:str) -> list[tuple[int, str]]:
        """Returns all cards given a language code"""
        self._ensure_cache(language_code)

        return [(card_id, name) for card_id, name, _ in self._cards_cache[language_code]]

    def search(self, text: str= "", language_code: str = "en") -> list[tuple[int, str]]:
        """Case-insensitive filtering for cards on search boxes"""
        self._ensure_cache(language_code)
        search_text = text.strip().lower()

        return [
            (card_id, name)
            for card_id, name, lowercase_name in self._cards_cache[language_code]
            if search_text in lowercase_name
        ]

    def clear_cache(self) -> None:
        """Invalidades cached card data"""
        self._cards_cache.clear()