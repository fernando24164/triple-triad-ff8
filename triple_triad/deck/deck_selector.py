from ..models.card import Card
from .presets import build_preset_deck, list_presets


def choose_preset_deck() -> list[Card]:
    """Prompt the player to pick a preset deck and return the cards."""
    """Prompt the player to pick a preset deck and return the cards."""
    presets = list_presets()
    print("\n  ── Preset Decks ──")
    for i, name in enumerate(presets, 1):
        cards = build_preset_deck(name)
        card_summary = ", ".join(c.name for c in cards[:3])
        if len(cards) > 3:
            card_summary += f" +{len(cards) - 3} more"
        print(f"  [{i}] {name:<16} — {card_summary}")

    while True:
        try:
            choice = int(input(f"\n  Choose preset [1-{len(presets)}]: ").strip())
            if 1 <= choice <= len(presets):
                selected = presets[choice - 1]
                deck = build_preset_deck(selected)
                print(f"\n  ✓ Selected: {selected.upper()}")
                return deck
            print(f"  ✗ Enter a number between 1 and {len(presets)}.")
        except ValueError:
            print("  ✗ Enter a number.")
