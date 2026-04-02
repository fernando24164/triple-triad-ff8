import random


def random_choice(empty_positions: list, cpu_hand: list):
    ci = random.randrange(len(cpu_hand))
    pos = random.choice(empty_positions)
    return ci, pos
