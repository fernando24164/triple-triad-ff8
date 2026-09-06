from ..models.card import Card

DECK_PRESETS: dict[str, list[str]] = {
    "Balanced": [
        "Mesmerize",
        "Cactuar",
        "Bomb",
        "Iron Giant",
        "Shiva",
    ],
    "Fire Power": [
        "SAM08G",
        "Bomb",
        "Hexadragon",
        "Ruby Dragon",
        "Ifrit",
    ],
    "Ice Wall": [
        "Glacial Eye",
        "Snow Lion",
        "Shiva",
        "Chimera",
        "Leviathan",
    ],
    "Rush": [
        "Gayla",
        "Thrustaevis",
        "Elvoret",
        "Pandemona",
        "Angelo",
    ],
    "Poison Squad": [
        "Anacondaur",
        "Tri-Face",
        "Blue Dragon",
        "Gerogero",
        "Doomtrain",
    ],
}


def list_presets() -> list[str]:
    """Return a list of available deck preset names."""
    return list(DECK_PRESETS.keys())


def build_preset_deck(preset_name: str) -> list[Card]:
    """Build a deck from a named preset. Returns 5 cards."""
    if preset_name not in DECK_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list_presets()}")
    card_names = DECK_PRESETS[preset_name]
    return [Card(name) for name in card_names]
