from .yugi import YUGI_DECKS
from .kaiba import KAIBA_DECKS
from .joey import JOEY_DECKS
from .solomon_muto import SOLOMON_MUTO_DECKS
from .tea import TÉA_GARDNER_DECKS

LIST_OF_DECKS = {
    "Yugi Muto": YUGI_DECKS,
    "Seto Kaiba": KAIBA_DECKS,
    "Joey Wheeler": JOEY_DECKS,
    "Solomon Muto": SOLOMON_MUTO_DECKS,
    "Téa Gardner": TÉA_GARDNER_DECKS
}

__all__ = ["LIST_OF_DECKS"]