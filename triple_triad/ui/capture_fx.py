from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from ..constants import GRID_SIZE
from ..models.board import Board
from ..models.card import Card

if TYPE_CHECKING:
    from blessed import Terminal

_FLASH = "\033[97;1m"  # bold bright white
_RESET = "\033[0m"

_ROW_RENDERERS = (
    Board._render_row1,
    Board._render_row2,
    Board._render_row3,
    Board._render_row4,
)


def _cell_origin(pos: int) -> tuple[int, int]:
    """First content-row index and column of a board cell within the text
    produced by ``Board.display()`` (top border is row 0)."""
    row, col = divmod(pos, GRID_SIZE)
    row_start = 1 + row * 5  # 4 content rows + 1 separator per grid row
    col_start = 1 + col * (Board.CELL_W + 1)
    return row_start, col_start


def _place(term: Terminal, cursor_row: int, row: int, col: int, content: str) -> str:
    """Escape sequence that writes ``content`` at (row, col) relative to the
    current cursor line (``cursor_row`` lines below row 0), then restores
    the cursor to where it started."""
    up = cursor_row - row
    return (
        term.move_up(up)
        + term.move_x(col)  # type: ignore[arg-type]
        + content
        + term.move_x(0)  # type: ignore[arg-type]
        + term.move_down(up)
    )


def _paint(
    term: Terminal,
    cursor_row: int,
    captures: list[tuple[int, Card]],
    content_at: Callable[[Card, int], str],
) -> None:
    frame = "".join(
        _place(term, cursor_row, _cell_origin(pos)[0] + r, _cell_origin(pos)[1], content_at(card, r))
        for pos, card in captures
        for r in range(4)
    )
    print(frame, end="", flush=True)


def animate_captures(
    term: Terminal | None,
    cursor_row: int,
    captures: list[tuple[int, Card]],
    new_owner: str | None,
) -> None:
    """Flip captured cards in place with a color-flash effect, then apply
    the ownership change. Falls back to a silent ownership swap when no
    interactive terminal is available.

    Slowed down (~1s total) and staged over three visually distinct beats
    so the flip reads clearly instead of flickering past unnoticed.

    Args:
        term: Active blessed Terminal, or None.
        cursor_row: Lines from the board's top border down to the current
            (blank) cursor position — i.e. how far up to travel to reach
            board row 0.
        captures: (pos, card) pairs being captured this turn.
        new_owner: Owner ('P' or 'CPU') the captured cards are flipping to.
    """
    if term is None or not term.does_styling or not captures:
        for _, ncard in captures:
            ncard.owner = new_owner
        return

    squeeze = _FLASH + f"{'▐▌':^{Board.CELL_W}}" + _RESET
    thin = _FLASH + f"{'│':^{Board.CELL_W}}" + _RESET

    # Beat 1: card shrinks edge-on (flip in profile), flashed bright white.
    _paint(term, cursor_row, captures, lambda _card, _r: squeeze)
    time.sleep(0.22)

    # Beat 2: card thins to a sliver — the card is now edge-on to the viewer.
    _paint(term, cursor_row, captures, lambda _card, _r: thin)
    time.sleep(0.18)

    for _, ncard in captures:
        ncard.owner = new_owner

    # Beat 3: reveal the card in its new owner's color (the flip's payoff).
    _paint(term, cursor_row, captures, lambda card, r: _ROW_RENDERERS[r](card))
    time.sleep(0.35)
