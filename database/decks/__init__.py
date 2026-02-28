from .yugi import YUGI_DECKS
from .kaiba import KAIBA_DECKS
from .joey import JOEY_DECKS
from .solomon_muto import SOLOMON_MUTO_DECKS
from .tea import TÉA_GARDNER_DECKS
from .tristan import TRISTAN_DECKS
from .leon import LEON_DECK

LIST_OF_DECKS = {
    "Yugi Muto": YUGI_DECKS,
    "Seto Kaiba": KAIBA_DECKS,
    "Joey Wheeler": JOEY_DECKS,
    "Solomon Muto": SOLOMON_MUTO_DECKS,
    "Téa Gardner": TÉA_GARDNER_DECKS,
    "Tristan Taylor": TRISTAN_DECKS,
    "Leon von Schroeder": LEON_DECK,
}

__all__ = ["LIST_OF_DECKS"]