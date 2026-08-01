from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ..constants import BOARD_CELLS, GRID_SIZE
from ..models.board import Board

if TYPE_CHECKING:
    from blessed import Terminal

_WASD = {"w": "KEY_UP", "a": "KEY_LEFT", "s": "KEY_DOWN", "d": "KEY_RIGHT"}
_ARROWS = ("KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT")


def next_empty_in_direction(board: Board, pos: int, key: str) -> int | None:
    """Return the nearest empty cell from ``pos`` moving toward ``key``,
    wrapping at the grid edges; None when that row/column has no empty cell.
    The current cell is never returned."""
    row, col = divmod(pos, GRID_SIZE)
    for step in range(1, GRID_SIZE):
        if key == "KEY_UP":
            r = (row - step) % GRID_SIZE
            cand = r * GRID_SIZE + col
        elif key == "KEY_DOWN":
            r = (row + step) % GRID_SIZE
            cand = r * GRID_SIZE + col
        elif key == "KEY_LEFT":
            c = (col - step) % GRID_SIZE
            cand = row * GRID_SIZE + c
        elif key == "KEY_RIGHT":
            c = (col + step) % GRID_SIZE
            cand = row * GRID_SIZE + c
        else:
            return None
        if board.is_empty(cand):
            return cand
    return None


def select_position(
    board: Board,
    term: Terminal | None,
    use_screen: bool,
    render: Callable[[int | None], None],
    start: int | None = None,
) -> int | None:
    """Interactively pick a board position with the arrow keys.

    Re-renders via ``render(highlight)`` on every move so the board shows a
    yellow border around the highlighted cell. Returns the chosen position,
    or None when the player cancels (Escape / r) to go back to card choice.
    Only meaningful for a styled (fullscreen-capable) terminal — callers
    keep the numeric prompt as the fallback otherwise.
    """
    if term is None or not use_screen:
        return None
    empty = [i for i in range(BOARD_CELLS) if board.is_empty(i)]
    if not empty:
        return None
    cur = start if start is not None and board.is_empty(start) else empty[0]

    with term.cbreak(), term.hidden_cursor():
        render(cur)
        while True:
            k = term.inkey()
            if not k:
                continue
            name = k.name or _WASD.get(str(k).lower())
            if name in _ARROWS:
                nxt = next_empty_in_direction(board, cur, name)
                if nxt is not None and nxt != cur:
                    cur = nxt
                    render(cur)
            elif name == "KEY_ENTER" or k == "\n":
                return cur
            elif name == "KEY_ESCAPE" or str(k).lower() == "r":
                return None
