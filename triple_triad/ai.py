# triple_triad/ai.py
import random

from .rules import simulate_capture


def cpu_choose(board, cpu_hand, rules, mode: str = "greedy"):
    """
    Choose a card and position for the CPU.

    Modes
    -----
    'random'  — pick a random card and position (easy difficulty)
    'greedy'  — pick the move that captures the most cards (medium/hard)
    """
    empty_positions = [i for i in range(9) if board.is_empty(i)]

    if not empty_positions:
        return 0, None

    if mode == "random":
        return _random_choice(empty_positions, cpu_hand)

    return _greedy_choice(board, cpu_hand, rules, empty_positions)


def _random_choice(empty_positions: list, cpu_hand: list):
    ci = random.randrange(len(cpu_hand))
    pos = random.choice(empty_positions)
    return ci, pos


def _greedy_choice(board, cpu_hand: list, rules, empty_positions: list):
    best_score = -1
    best_card_idx = 0
    best_pos = empty_positions[0]

    for ci, card in enumerate(cpu_hand):
        for pos in empty_positions:
            # Simulate capture without copying objects - much faster
            score = simulate_capture(board, pos, card, "CPU", rules)
            if score > best_score:
                best_score = score
                best_card_idx = ci
                best_pos = pos

    return best_card_idx, best_pos