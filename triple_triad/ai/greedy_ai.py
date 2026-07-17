import random
from collections.abc import Collection

from ..engine.rules import simulate_capture
from ..models.board import Board
from ..models.card import Card


def greedy_choice(
    board: Board,
    cpu_hand: list[Card],
    rules: Collection[str],
    empty_positions: list[int],
    randomness: float = 0.0,
) -> tuple[int, int]:
    """Pick a move via 1-ply capture scoring, with optional gradual randomness.

    ``randomness`` (0.0-1.0) widens the pool of "good enough" moves considered
    before picking: 0.0 always takes the single highest-scoring move
    (deterministic, first found — matches the classic greedy behavior).
    Above 0.0, moves scoring within a tolerance of the best score are also
    eligible, weighted toward the higher-scoring ones, so the CPU occasionally
    plays a slightly-suboptimal move instead of being perfectly predictable.
    A move that captures at least one card is never passed over for a
    zero-capture move, regardless of ``randomness``.
    """
    moves = [
        (ci, pos, simulate_capture(board, pos, card, "CPU", rules))
        for ci, card in enumerate(cpu_hand)
        for pos in empty_positions
    ]
    best_score = max(score for _, _, score in moves)

    if randomness <= 0 or best_score <= 0:
        best_ci, best_pos, _ = max(moves, key=lambda m: m[2])
        return best_ci, best_pos

    floor = max(1, best_score - round(randomness * best_score))
    pool = [m for m in moves if m[2] >= floor]
    weights = [score + 1 for _, _, score in pool]
    ci, pos, _ = random.choices(pool, weights=weights, k=1)[0]
    return ci, pos
