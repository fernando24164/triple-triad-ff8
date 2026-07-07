from collections.abc import Collection

from ..constants import BOARD_CELLS
from ..models.board import Board
from ..models.card import Card
from .greedy_ai import greedy_choice
from .minimax_ai import minimax_choice
from .random_ai import random_choice


def cpu_choose(
    board: Board,
    cpu_hand: list[Card],
    rules: Collection[str],
    mode: str = "greedy",
    player_hand: list[Card] | None = None,
    depth: int = 1,
) -> tuple[int, int | None]:
    """
    Choose a card and position for the CPU.

    Modes
    -----
    'random'   — pick a random card and position (easy difficulty)
    'greedy'   — pick the move that captures the most cards now (1-ply)
    'minimax'  — depth-limited alpha-beta lookahead (hard difficulty)

    'minimax' requires ``player_hand`` (to model the player's replies) and uses
    ``depth`` as the search depth. Reading the player's hand is only fair when
    it's already visible on-screen, so minimax only activates when the 'Open'
    rule is in ``rules``; otherwise (or if ``player_hand`` is missing) it
    safely falls back to greedy.
    """
    empty_positions = [i for i in range(BOARD_CELLS) if board.is_empty(i)]

    if not empty_positions:
        return 0, None

    if mode == "random":
        return random_choice(empty_positions, cpu_hand)

    if mode == "minimax" and player_hand is not None and "Open" in rules:
        return minimax_choice(
            board, cpu_hand, player_hand, rules, empty_positions, depth
        )

    return greedy_choice(board, cpu_hand, rules, empty_positions)
