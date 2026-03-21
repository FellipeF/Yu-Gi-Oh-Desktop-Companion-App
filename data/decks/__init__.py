from .anubis import ANUBIS_DECK
from .arkana import ARKANA_DECKS
from .dartz import DARTZ_DECKS
from .duke import DUKE_DECKS
from .lumis import LUMIS_DECKS
from .mai import MAI_DECKS
from .mako import MAKO_DECKS
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
    "yugi_muto": YUGI_DECKS,
    "seto_kaiba": KAIBA_DECKS,
    "joey_wheeler": JOEY_DECKS,
    "solomon_muto": SOLOMON_MUTO_DECKS,
    "tea_gardner": TEA_GARDNER_DECKS,
    "tristan_taylor": TRISTAN_DECKS,
    "leon_von_schroeder": LEON_DECK,
    "maximillion_pegasus": PEGASUS_DECKS,
    "lumis": LUMIS_DECKS,
    "umbra": UMBRA_DECKS,
    "dartz": DARTZ_DECKS,
    "anubis": ANUBIS_DECK,
    "duke_devlin": DUKE_DECKS,
    "arkana": ARKANA_DECKS,
    "weevil_underwood": WEEVIL_DECKS,
    "mai_valentine": MAI_DECKS,
    "mako_tsunami": MAKO_DECKS,
}

__all__ = ["LIST_OF_DECKS"]