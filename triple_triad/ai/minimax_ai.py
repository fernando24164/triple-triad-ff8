from collections.abc import Collection

from ..constants import BOARD_CELLS
from ..engine.rules import resolve_captures, simulate_capture
from ..models.board import Board
from ..models.card import Card

# Integer sentinels keep the search fully int-typed (no float inf).
_NEG_INF = -10**9
_POS_INF = 10**9


def _evaluate(board: Board) -> int:
    """Board-owner differential from the CPU's perspective (``#CPU - #P``).

    Mirrors :func:`triple_triad.engine.scoring.calculate_final_scores`. On a
    full board this exactly determines the winner; at a depth cutoff it is a
    sound proxy for board control.
    """
    cpu = 0
    p = 0
    for card in board.cells:
        if card is None:
            continue
        if card.owner == "CPU":
            cpu += 1
        elif card.owner == "P":
            p += 1
    return cpu - p


def _apply_move(
    board: Board, pos: int, card: Card, mover: str, rules: Collection[str]
) -> list[tuple[Card, str | None]]:
    """Place ``card`` at ``pos`` for ``mover`` and flip captured neighbors.

    The card must already be removed from its hand by the caller. Returns the
    list of ``(captured_card, previous_owner)`` pairs so the move can be undone.
    """
    card.owner = mover
    board.place(pos, card)

    captures, _events = resolve_captures(board, pos, card, rules)
    flipped: list[tuple[Card, str | None]] = []
    for _npos, ncard in captures:
        flipped.append((ncard, ncard.owner))
        ncard.owner = mover
    return flipped


def _undo_move(
    board: Board,
    pos: int,
    card: Card,
    prev_owner: str | None,
    flipped: list[tuple[Card, str | None]],
) -> None:
    """Reverse an :func:`_apply_move`, restoring the board and all owners."""
    for ncard, old_owner in flipped:
        ncard.owner = old_owner
    board.cells[pos] = None
    card.owner = prev_owner


def _search(
    board: Board,
    cpu_hand: list[Card],
    player_hand: list[Card],
    rules: Collection[str],
    depth: int,
    alpha: int,
    beta: int,
    maximizing: bool,
) -> int:
    """Alpha-beta minimax. Returns the CPU-perspective value of ``board``."""
    empty = [i for i in range(BOARD_CELLS) if board.is_empty(i)]
    if depth == 0 or not empty:
        return _evaluate(board)

    hand = cpu_hand if maximizing else player_hand
    if not hand:
        # Side to move has no cards; let the other side continue. The other
        # hand is guaranteed non-empty here (10 cards vs 9 cells), so this
        # cannot loop.
        return _search(
            board, cpu_hand, player_hand, rules, depth, alpha, beta, not maximizing
        )

    mover = "CPU" if maximizing else "P"

    # Move ordering: try high-capture moves first to maximize pruning.
    moves = [
        (ci, pos, simulate_capture(board, pos, hand[ci], mover, rules))
        for ci in range(len(hand))
        for pos in empty
    ]
    moves.sort(key=lambda m: m[2], reverse=True)

    if maximizing:
        value = _NEG_INF
        for ci, pos, _score in moves:
            card = hand.pop(ci)
            prev_owner = card.owner
            flipped = _apply_move(board, pos, card, mover, rules)
            value = max(
                value,
                _search(
                    board, cpu_hand, player_hand, rules, depth - 1, alpha, beta, False
                ),
            )
            _undo_move(board, pos, card, prev_owner, flipped)
            hand.insert(ci, card)

            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    value = _POS_INF
    for ci, pos, _score in moves:
        card = hand.pop(ci)
        prev_owner = card.owner
        flipped = _apply_move(board, pos, card, mover, rules)
        value = min(
            value,
            _search(
                board, cpu_hand, player_hand, rules, depth - 1, alpha, beta, True
            ),
        )
        _undo_move(board, pos, card, prev_owner, flipped)
        hand.insert(ci, card)

        beta = min(beta, value)
        if alpha >= beta:
            break
    return value


def minimax_choice(
    board: Board,
    cpu_hand: list[Card],
    player_hand: list[Card],
    rules: Collection[str],
    empty_positions: list[int],
    depth: int,
) -> tuple[int, int]:
    """Pick the CPU's best ``(card_index, position)`` via minimax search.

    ``depth`` is clamped to the number of empty cells, so late-game searches
    solve the remaining position exactly without wasted work.
    """
    effective_depth = max(1, min(depth, len(empty_positions)))

    best_score = _NEG_INF
    best_card_idx = 0
    best_pos = empty_positions[0]

    # Root move ordering (same rationale as inside _search).
    root_moves = [
        (ci, pos, simulate_capture(board, pos, cpu_hand[ci], "CPU", rules))
        for ci in range(len(cpu_hand))
        for pos in empty_positions
    ]
    root_moves.sort(key=lambda m: m[2], reverse=True)

    alpha = _NEG_INF
    for ci, pos, _score in root_moves:
        card = cpu_hand.pop(ci)
        prev_owner = card.owner
        flipped = _apply_move(board, pos, card, "CPU", rules)
        score = _search(
            board,
            cpu_hand,
            player_hand,
            rules,
            effective_depth - 1,
            alpha,
            _POS_INF,
            False,
        )
        _undo_move(board, pos, card, prev_owner, flipped)
        cpu_hand.insert(ci, card)

        if score > best_score:
            best_score = score
            best_card_idx = ci
            best_pos = pos
        alpha = max(alpha, best_score)

    return best_card_idx, best_pos
