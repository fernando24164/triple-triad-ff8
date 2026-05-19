import random
from typing import cast

from ..constants import DECK_SIZE
from ..data.cards import CARDS
from ..models.card import Card

DIFFICULTY_CONFIG = {
    "easy": {
        "player_max_level": 9,  # Player can pick any card
        "cpu_min_level": 1,
        "cpu_max_level": 3,  # CPU stuck with weak cards
        "cpu_ai": "random",  # CPU plays randomly
        "description": "CPU uses weak cards (Lv 1-3) and plays randomly",
    },
    "medium": {
        "player_max_level": 9,
        "cpu_min_level": 4,
        "cpu_max_level": 6,  # CPU uses mid-tier cards
        "cpu_ai": "greedy",  # CPU plays greedy
        "description": "CPU uses mid-tier cards (Lv 4-6) and plays smart",
    },
    "hard": {
        "player_max_level": 9,
        "cpu_min_level": 7,
        "cpu_max_level": 10,  # CPU uses top-tier cards
        "cpu_ai": "greedy",  # CPU plays greedy
        "description": "CPU uses elite cards (Lv 7-10) and plays optimally",
    },
}


def build_starter_deck() -> list[Card]:
    """Return a list of DECK_SIZE random low-level cards for the player."""
    low_cards = [name for name, data in CARDS.items() if data.level <= 3]
    chosen = random.sample(low_cards, min(DECK_SIZE, len(low_cards)))
    return [Card(name) for name in chosen]


def build_cpu_deck(difficulty: str = "medium") -> list[Card]:
    """Build a CPU deck based on difficulty config."""
    cfg = DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["medium"])
    pool = [
        name
        for name, data in CARDS.items()
        if cast(int, cfg["cpu_min_level"])
        <= data.level
        <= cast(int, cfg["cpu_max_level"])
    ]
    if len(pool) < DECK_SIZE:
        pool = sorted(CARDS.keys(), key=lambda n: CARDS[n].level)
    chosen = random.sample(pool, DECK_SIZE)
    return [Card(name) for name in chosen]


def get_cpu_ai_mode(difficulty: str) -> str:
    """Return the AI mode string for this difficulty."""
    return cast(
        str, DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["medium"])["cpu_ai"]
    )


def build_random_deck() -> list[Card]:
    """Build a deck of DECK_SIZE random cards from the full card pool."""
    all_names = list(CARDS.keys())
    chosen = random.sample(all_names, min(DECK_SIZE, len(all_names)))
    return [Card(name) for name in chosen]
