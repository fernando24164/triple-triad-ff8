from ..models.card import Card

DECK_PRESETS: dict[str, list[str]] = {
    "Balanced": [
        "Mesmerize",  # Lv2, no element, balanced stats
        "Cactuar",  # Lv3, no element
        "Bomb",  # Lv4, Fire
        "Iron Giant",  # Lv5, no element, strong
        "Shiva",  # Lv8, Ice, high stats
    ],
    "Fire Power": [
        "SAM08G",  # Lv3, Fire
        "Bomb",  # Lv4, Fire
        "Hexadragon",  # Lv4, Fire
        "Ruby Dragon",  # Lv5, Fire
        "Ifrit",  # Lv8, Fire
    ],
    "Ice Wall": [
        "Glacial Eye",  # Lv2, Ice
        "Snow Lion",  # Lv3, Ice
        "Shiva",  # Lv8, Ice
        "Chimera",  # Lv5, Water (cold theme)
        "Leviathan",  # Lv9, Water (cold theme)
    ],
    "Rush": [
        "Gayla",  # Lv1, no element, fast low-level
        "Thrustaevis",  # Lv2, Wind
        "Elvoret",  # Lv6, Wind
        "Pandemona",  # Lv9, Wind
        "Angelo",  # Lv8, no element
    ],
    "Poison Squad": [
        "Anacondaur",  # Lv2, Poison
        "Tri-Face",  # Lv3, Poison
        "Blue Dragon",  # Lv4, Poison
        "Gerogero",  # Lv6, Poison
        "Doomtrain",  # Lv9, Poison
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
