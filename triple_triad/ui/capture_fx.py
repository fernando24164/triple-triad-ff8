from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from ..constants import GRID_SIZE
from ..models.board import Board
from ..models.card import Card
from ..synth.sfx import play_capture_banner

if TYPE_CHECKING:
    from blessed import Terminal

_FLASH = "\033[97;1m"  # bold bright white
_GREEN = "\033[92;1m"  # bold bright green — player capture
_RED = "\033[91;1m"  # bold bright red — CPU/opponent capture
_RESET = "\033[0m"

_BANNER_WORD = "CAPTURED!"

# 5-row block-letter font. '#' marks a filled cell; swapping it for a
# lighter shade character at render time is what drives the materialize
# and dissolve effects without needing a separate glyph set.
_FONT: dict[str, tuple[str, str, str, str, str]] = {
    "C": (" ####", "#    ", "#    ", "#    ", " ####"),
    "A": (" ### ", "#   #", "#####", "#   #", "#   #"),
    "P": ("#### ", "#   #", "#### ", "#    ", "#    "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", " ### "),
    "R": ("#### ", "#   #", "#### ", "#  # ", "#   #"),
    "E": ("#####", "#    ", "#### ", "#    ", "#####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#### "),
    "F": ("#####", "#    ", "#### ", "#    ", "#    "),
    "V": ("#   #", "#   #", "#   #", " # # ", "  #  "),
    "I": ("###", " # ", " # ", " # ", "###"),
    "O": (" ### ", "#   #", "#   #", "#   #", " ### "),
    "Y": ("#   #", " # # ", "  #  ", "  #  ", "  #  "),
    "!": (" # ", " # ", " # ", "   ", " # "),
    " ": ("   ", "   ", "   ", "   ", "   "),
}

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
    col_offset: int,
    captures: list[tuple[int, Card]],
    content_at: Callable[[Card, int], str],
) -> None:
    frame = "".join(
        _place(
            term,
            cursor_row,
            _cell_origin(pos)[0] + r,
            _cell_origin(pos)[1] + col_offset,
            content_at(card, r),
        )
        for pos, card in captures
        for r in range(4)
    )
    print(frame, end="", flush=True)


def _build_art(word: str, pixel: str) -> list[str]:
    """Render `word` as 5-row block-letter ASCII art, filling every lit
    cell with `pixel`. Letters are separated by a single blank column."""
    glyphs = [_FONT.get(ch, _FONT[" "]) for ch in word.upper()]
    return [
        " ".join(
            "".join(pixel if c == "#" else " " for c in glyph[row]) for glyph in glyphs
        )
        for row in range(5)
    ]


def _paint_art(term: Terminal, row: int, col: int, lines: list[str], color: str) -> None:
    visible = max(0, term.width - col)
    frame = "".join(
        term.move_yx(row + i, col) + color + line[:visible] + _RESET
        for i, line in enumerate(lines)
    )
    print(frame, end="", flush=True)


def _show_banner(term: Terminal, word: str, color: str) -> None:
    """Generic ASCII-art banner effect, shared by the capture and victory
    banners: materializes center-screen out of faint dust, flickers a
    couple of times for a pop, then dissolves back out. Nothing is left on
    screen when this returns — the caller's redraw afterward is just a
    safety net."""
    solid = _build_art(word, "█")
    width = len(solid[0])
    col = max(0, (term.width - width) // 2)
    row = max(0, min(term.height - 5, term.height // 2 - 2))

    # Materialize: faint dust condenses into the full shape, white easing
    # into the banner's color.
    for shade, c in (("░", _FLASH), ("▒", _FLASH), ("▓", color)):
        _paint_art(term, row, col, _build_art(word, shade), c)
        time.sleep(0.07)

    # Pop: a couple of bright/color flickers on the fully-formed banner.
    for c in (_FLASH, color, _FLASH, color):
        _paint_art(term, row, col, solid, c)
        time.sleep(0.11)

    # Dissolve: the shape thins back down to nothing.
    for shade in ("▓", "▒", "░", " "):
        _paint_art(term, row, col, _build_art(word, shade), color)
        time.sleep(0.07)


def _flash_banner(term: Terminal, new_owner: str | None) -> None:
    """Casino-style 'CAPTURED!' banner with a whoosh sound, rendered as
    block-letter ASCII art via `_show_banner`."""
    owner_color = _GREEN if new_owner == "P" else _RED
    play_capture_banner()
    _show_banner(term, _BANNER_WORD, owner_color)


def show_victory_banner(term: Terminal | None) -> None:
    """ASCII-art 'VICTORY!' banner for a player match win: materializes and
    dissolves center-screen the same way the capture banner does. No-op
    when no interactive terminal is available. The caller should redraw
    the game-over screen afterward to clear any leftover banner artifacts.
    """
    if term is None or not term.does_styling:
        return
    _show_banner(term, "VICTORY!", _GREEN)


def show_defeat_banner(term: Terminal | None) -> None:
    """ASCII-art 'DEFEAT!' banner for a match loss: materializes and
    dissolves center-screen the same way the capture banner does. No-op
    when no interactive terminal is available. The caller should redraw
    the game-over screen afterward to clear any leftover banner artifacts.
    """
    if term is None or not term.does_styling:
        return
    _show_banner(term, "DEFEAT!", _RED)


def animate_captures(
    term: Terminal | None,
    cursor_row: int,
    captures: list[tuple[int, Card]],
    new_owner: str | None,
    col_offset: int = 0,
) -> None:
    """Flip captured cards in place with a color-flash effect, then apply
    the ownership change and pop up a center-screen ASCII-art "CAPTURED!"
    banner. Falls back to a silent ownership swap when no interactive
    terminal is available.

    Staged over four visually distinct beats (~1.5s total) so the flip and
    banner read clearly instead of flickering past unnoticed. The banner
    materializes and dissolves on its own, so nothing is left on screen
    when this returns — the caller's redraw afterward is just a safety net.

    Args:
        term: Active blessed Terminal, or None.
        cursor_row: Lines from the board's top border down to the current
            (blank) cursor position — i.e. how far up to travel to reach
            board row 0.
        captures: (pos, card) pairs being captured this turn.
        new_owner: Owner ('P' or 'CPU') the captured cards are flipping to.
        col_offset: Columns the board was shifted right for horizontal
            centering — added to every cell's column so the flip lands on
            the actual on-screen board instead of column 0.
    """
    if term is None or not term.does_styling or not captures:
        for _, ncard in captures:
            ncard.owner = new_owner
        return

    squeeze = _FLASH + f"{'▐▌':^{Board.CELL_W}}" + _RESET
    thin = _FLASH + f"{'│':^{Board.CELL_W}}" + _RESET

    # Beat 1: card shrinks edge-on (flip in profile), flashed bright white.
    _paint(term, cursor_row, col_offset, captures, lambda _card, _r: squeeze)
    time.sleep(0.22)

    # Beat 2: card thins to a sliver — the card is now edge-on to the viewer.
    _paint(term, cursor_row, col_offset, captures, lambda _card, _r: thin)
    time.sleep(0.18)

    for _, ncard in captures:
        ncard.owner = new_owner

    # Beat 3: reveal the card in its new owner's color (the flip's payoff).
    _paint(term, cursor_row, col_offset, captures, lambda card, r: _ROW_RENDERERS[r](card))
    time.sleep(0.2)

    # Beat 4: an ASCII-art "CAPTURED!" banner materializes, flickers, and
    # dissolves center-screen.
    _flash_banner(term, new_owner)
