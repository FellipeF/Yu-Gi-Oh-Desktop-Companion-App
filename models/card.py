from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class CardDetails:
    card_id: int
    name: str | None
    description: str
    card_type: str | None
    readable_type: str | None
    race: str | None
    attribute: str | None
    atk: int | None
    defense: int | None
    level: int | None
    scale: int | None
    linkval: int | None
    linkmarkers: str | None