from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ..constants import BOARD_CELLS, GRID_SIZE
from ..models.board import Board

if TYPE_CHECKING:
    from blessed import Terminal

_WASD = {"w": "KEY_UP", "a": "KEY_LEFT", "s": "KEY_DOWN", "d": "KEY_RIGHT"}
_ARROWS = ("KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT")


class QuitGameError(Exception):
    """Raised when the player presses 'q' to abandon the current match."""


def _cyclic_dist(a: int, b: int) -> int:
    """Shortest wrapped distance between two grid coordinates."""
    d = (a - b) % GRID_SIZE
    return min(d, GRID_SIZE - d)


def next_empty_in_direction(board: Board, pos: int, key: str) -> int | None:
    """Return the nearest empty cell from ``pos`` moving toward ``key``.

    Lines (rows for UP/DOWN, columns for LEFT/RIGHT) are scanned in the
    pressed direction, wrapping around the grid edges. The first line
    containing any empty cell wins, and the cursor snaps to the empty cell
    in that line nearest to the current one. This keeps every empty cell
    reachable — e.g. two free cells in opposite corners — which a plain
    same-row/column scan can never do. Returns None when no other empty
    cell exists. The current cell is never returned.
    """
    if key not in ("KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"):
        return None
    row, col = divmod(pos, GRID_SIZE)
    row_primary = key in ("KEY_UP", "KEY_DOWN")
    step = 1 if key in ("KEY_DOWN", "KEY_RIGHT") else -1
    line_anchor = row if row_primary else col
    sec_anchor = col if row_primary else row

    for dist in range(1, GRID_SIZE + 1):
        line = (line_anchor + step * dist) % GRID_SIZE
        if row_primary:
            line_cells = [(line * GRID_SIZE + c, c) for c in range(GRID_SIZE)]
        else:
            line_cells = [(r * GRID_SIZE + line, r) for r in range(GRID_SIZE)]
        candidates = [(p, s) for p, s in line_cells if p != pos and board.is_empty(p)]
        if not candidates:
            continue
        candidates.sort(key=lambda ps: (_cyclic_dist(sec_anchor, ps[1]), ps[0]))
        return candidates[0][0]
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
    Raises :class:`QuitGameError` when the player presses 'q' to abandon the match.
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
            elif str(k).lower() == "q":
                raise QuitGameError
            elif name == "KEY_ESCAPE" or str(k).lower() == "r":
                return None
