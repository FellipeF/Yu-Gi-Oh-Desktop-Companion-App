from .yugi import YUGI_DECKS
from .kaiba import KAIBA_DECKS
from .joey import JOEY_DECKS

LIST_OF_DECKS = {
    "Yugi Muto": YUGI_DECKS,
    "Seto Kaiba": KAIBA_DECKS,
    "Joey Wheeler": JOEY_DECKS
}

__all__ = ["LIST_OF_DECKS"]