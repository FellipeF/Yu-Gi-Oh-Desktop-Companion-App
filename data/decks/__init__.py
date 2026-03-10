from .anubis import ANUBIS_DECK
from .arkana import ARKANA_DECKS
from .dartz import DARTZ_DECKS
from .duke import DUKE_DECKS
from .lumis import LUMIS_DECKS
from .mai import MAI_DECKS
from .umbra import UMBRA_DECKS
from .weevil import WEEVIL_DECKS
from .yugi import YUGI_DECKS
from .kaiba import KAIBA_DECKS
from .joey import JOEY_DECKS
from .solomon_muto import SOLOMON_MUTO_DECKS
from .tea import TEA_GARDNER_DECKS
from .tristan import TRISTAN_DECKS
from .leon import LEON_DECK
from .pegasus import PEGASUS_DECKS

LIST_OF_DECKS = {
    "Yugi Muto": YUGI_DECKS,
    "Seto Kaiba": KAIBA_DECKS,
    "Joey Wheeler": JOEY_DECKS,
    "Solomon Muto": SOLOMON_MUTO_DECKS,
    "Téa Gardner": TEA_GARDNER_DECKS,
    "Tristan Taylor": TRISTAN_DECKS,
    "Leon von Schroeder": LEON_DECK,
    "Maximillion Pegasus": PEGASUS_DECKS,
    "Lumis": LUMIS_DECKS,
    "Umbra": UMBRA_DECKS,
    "Dartz": DARTZ_DECKS,
    "Anubis": ANUBIS_DECK,
    "Duke Devlin": DUKE_DECKS,
    "Arkana": ARKANA_DECKS,
    "Weevil Underwood": WEEVIL_DECKS,
    "Mai Valentine": MAI_DECKS,
}

__all__ = ["LIST_OF_DECKS"]