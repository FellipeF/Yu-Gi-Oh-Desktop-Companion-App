from data.gx.aster_phoenix import ASTER_PHOENIX_DECKS
from data.gx.decks.dancing_fairy import DANCING_FAIRY_DECK
from data.gx.decks.jasmine import JASMINE_DECKS
from data.gx.decks.jean_louis_bonaparte import JEAN_LOUIS_BONAPARTE_DECKS
from data.gx.decks.sadie import SADIE_DECKS
from data.gx.decks.slade_princeton import SLADE_PRINCETON_DECKS
from data.gx.decks.torrey import TORREY_DECKS

LIST_OF_DECKS_GX = {
    "jean_louis_bonaparte": JEAN_LOUIS_BONAPARTE_DECKS,
    "slade_princeton": SLADE_PRINCETON_DECKS,
    "sadie": SADIE_DECKS,
    "torrey": TORREY_DECKS,
    "aster_phoenix": ASTER_PHOENIX_DECKS,
    "dancing_fairy": DANCING_FAIRY_DECK,
    "jasmine": JASMINE_DECKS,
}

__all__ = ["LIST_OF_DECKS_GX"]