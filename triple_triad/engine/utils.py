import random

from ..models.card import Card


def random_rules() -> set[str]:
    """Pick a random subset of rules for a tournament game."""
    available = ["Open", "Same", "Plus", "Random"]
    count = random.randint(0, 2)
    return set(random.sample(available, count))


def reset_card_owners(*hands: list[Card]) -> None:
    """Reset all hands in the given list to have no owner."""
    for hand in hands:
        for card in hand:
            card.owner = None
