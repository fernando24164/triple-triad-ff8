from ..constants import BOARD_CELLS
from .greedy_ai import greedy_choice
from .random_ai import random_choice


def cpu_choose(board, cpu_hand, rules, mode: str = "greedy"):
    """
    Choose a card and position for the CPU.

    Modes
    -----
    'random'  — pick a random card and position (easy difficulty)
    'greedy'  — pick the move that captures the most cards (medium/hard)
    """
    empty_positions = [i for i in range(BOARD_CELLS) if board.is_empty(i)]

    if not empty_positions:
        return 0, None

    if mode == "random":
        return random_choice(empty_positions, cpu_hand)

    return greedy_choice(board, cpu_hand, rules, empty_positions)
