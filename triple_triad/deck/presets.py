from ..models.card import Card

DECK_PRESETS: dict[str, list[str]] = {
    "Balanced": [
        "Mesmerize",  # Lv3, no element, balanced stats
        "Cactuar",  # Lv4, no element
        "Bomb",  # Lv5, Fire
        "Iron Giant",  # Lv6, no element, strong
        "Shiva",  # Lv9, Ice, high stats
    ],
    "Fire Power": [
        "SAM08G",  # Lv4, Fire
        "Bomb",  # Lv5, Fire
        "Hexadragon",  # Lv5, Fire
        "Ruby Dragon",  # Lv6, Fire
        "Ifrit",  # Lv9, Fire
    ],
    "Ice Wall": [
        "Glacial Eye",  # Lv3, Ice
        "Snow Lion",  # Lv4, Ice
        "Shiva",  # Lv9, Ice
        "Chimera",  # Lv6, Water (cold theme)
        "Leviathan",  # Lv9, Water (cold theme)
    ],
    "Thunder Rush": [
        "Gayla",  # Lv2, Thunder
        "Cockatrice",  # Lv2, Thunder
        "Thrustaevis",  # Lv3, Wind
        "Blitz",  # Lv5, Thunder
        "Quezacotl",  # Lv9, Thunder
    ],
    "Poison Squad": [
        "Anacondaur",  # Lv3, Poison
        "Tri-Face",  # Lv4, Poison
        "Blue Dragon",  # Lv5, Poison
        "Gerogero",  # Lv7, Poison
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
