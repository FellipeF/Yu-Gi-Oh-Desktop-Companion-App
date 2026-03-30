"""Controls and cache searched cards on CardsFrame and CustomDeckEditorFrame search boxes. This cache is
written as a dictionary, where the language_code contains id, original name and the lower-case name so that
a .lower() doesn't need to be called everytime a letter is typed"""

from database.queries import search_cards

class CardSearchService:
    def __init__(self):
        self._cards_cache: dict[str, list[tuple[int, str, str]]] = {}

    def get_all_cards(self, language_code:str) -> list[tuple[int, str]]:
        """Creates or uses cache for cards instead of querying the db everytime"""
        if language_code not in self._cards_cache:
            cards = search_cards(language=language_code)

            self._cards_cache[language_code] = [(card_id, card_name, card_name.lower()) for card_id, card_name in cards]

        return [(card_id, card_name) for card_id, card_name, _ in self._cards_cache[language_code]]

    def search(self, text: str= "", language_code: str = "en") -> list[tuple[int, str]]:
        """Case-insensitive filtering for cards on search boxes"""
        self.get_all_cards(language_code)
        search_text = text.strip().lower()

        if not search_text:
            # Currently, no bottleneck detected for showing all cards when list is loaded, but could always
            # Use a limit parameter if needed.
            return [
                (card_id, card_name)
                for card_id, card_name, _ in self._cards_cache[language_code]
            ]

        return [
            (card_id, card_name)
            for card_id, card_name, lowercase_name in self._cards_cache[language_code]
            if search_text in lowercase_name
        ]