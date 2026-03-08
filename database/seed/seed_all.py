from database.seed.seed_cards import populate_cards
from database.seed.seed_duelists import populate_duelists
from database.seed.seed_decks import populate_decks
from database.seed.seed_decks_translations import (
    populate_deck_category_translations,
    populate_duelist_deck_translations,
)

def seed_all(language: str = "en") -> None:
    populate_cards(language)
    populate_duelists()
    populate_decks()
    populate_deck_category_translations()
    populate_duelist_deck_translations()