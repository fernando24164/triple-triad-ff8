from collections.abc import Collection

from ..constants import BOARD_CELLS
from ..models.board import Board
from ..models.card import Card
from .greedy_ai import greedy_choice
from .random_ai import random_choice


def cpu_choose(
    board: Board,
    cpu_hand: list[Card],
    rules: Collection[str],
    mode: str = "greedy",
    randomness: float = 0.0,
) -> tuple[int, int | None]:
    """
    Choose a card and position for the CPU.

    Modes
    -----
    'random'   — pick a random card and position (easy difficulty)
    'greedy'   — pick the move that captures the most cards now (1-ply)

    ``randomness`` (0.0-1.0) only affects 'greedy' mode: see
    :func:`.greedy_ai.greedy_choice` for its effect.
    """
    empty_positions = [i for i in range(BOARD_CELLS) if board.is_empty(i)]

    if not empty_positions:
        return 0, None

    if mode == "random":
        return random_choice(empty_positions, cpu_hand)

    return greedy_choice(board, cpu_hand, rules, empty_positions, randomness)
