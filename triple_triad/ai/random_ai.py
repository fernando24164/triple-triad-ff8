import random

from ..models.card import Card


def random_choice(empty_positions: list[int], cpu_hand: list[Card]) -> tuple[int, int]:
    ci = random.randrange(len(cpu_hand))
    pos = random.choice(empty_positions)
    return ci, pos
