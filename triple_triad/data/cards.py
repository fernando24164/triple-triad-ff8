import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

CARDS_PATH = Path(__file__).parent / "cards.json"


class Element(StrEnum):
    """Card element types (str enum for backward compatibility)."""

    THUNDER = "Thunder"
    EARTH = "Earth"
    ICE = "Ice"
    WIND = "Wind"
    POISON = "Poison"
    FIRE = "Fire"
    WATER = "Water"
    HOLY = "Holy"


@dataclass(frozen=True)
class CardStats:
    """Immutable card statistics."""

    name: str
    top: int
    right: int
    bottom: int
    left: int
    element: Element | None
    level: int


CARDS: dict[str, CardStats] = {}
if not CARDS_PATH.exists():
    raise FileNotFoundError(
        f"Missing card data file: {CARDS_PATH.resolve()}\n"
        f"Ensure {CARDS_PATH.name} exists in {CARDS_PATH.parent.resolve()}"
    )
try:
    _raw = json.loads(CARDS_PATH.read_text())
except json.JSONDecodeError as e:
    raise RuntimeError(
        f"Corrupt card data file: {CARDS_PATH.resolve()}\n"
        f"JSON error at line {e.lineno}, column {e.colno}: {e.msg}"
    ) from e
for name, data in _raw.items():
    element = Element(data["element"]) if data["element"] else None
    CARDS[name] = CardStats(
        name=data["name"],
        top=data["top"],
        right=data["right"],
        bottom=data["bottom"],
        left=data["left"],
        element=element,
        level=data["level"],
    )
