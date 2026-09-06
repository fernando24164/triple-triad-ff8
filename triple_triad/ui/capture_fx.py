from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from ..constants import GRID_SIZE
from ..models.card import Card
from ..models.player import Player
from ..synth.sfx import play_capture_banner
from .particles import show_capture_particles
from .render import CELL_W, render_row1, render_row2, render_row3, render_row4

if TYPE_CHECKING:
    from blessed import Terminal

_FLASH = "\033[97;1m"
_GREEN = "\033[92;1m"
_RED = "\033[91;1m"
_YELLOW = "\033[93;1m"
_RESET = "\033[0m"

_BANNER_WORD = "CAPTURED!"

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
    "W": ("#   #", "#   #", "# # #", "# # #", " # # "),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#####"),
    "S": (" ####", "#    ", " ### ", "    #", "#### "),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#### ", "#   #", "#### "),
    "!": (" # ", " # ", " # ", "   ", " # "),
    " ": ("   ", "   ", "   ", "   ", "   "),
}

_ROW_RENDERERS = (
    render_row1,
    render_row2,
    render_row3,
    render_row4,
)


def _cell_origin(pos: int) -> tuple[int, int]:
    """First content-row index and column of a board cell within the text
    produced by ``render_board()`` (top border is row 0)."""
    row, col = divmod(pos, GRID_SIZE)
    row_start = 1 + row * 5
    col_start = 1 + col * (CELL_W + 1)
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


def _paint_art(
    term: Terminal, row: int, col: int, lines: list[str], color: str
) -> None:
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

    for shade, c in (("░", _FLASH), ("▒", _FLASH), ("▓", color)):
        _paint_art(term, row, col, _build_art(word, shade), c)
        time.sleep(0.07)

    for c in (_FLASH, color, _FLASH, color):
        _paint_art(term, row, col, solid, c)
        time.sleep(0.11)

    for shade in ("▓", "▒", "░", " "):
        _paint_art(term, row, col, _build_art(word, shade), color)
        time.sleep(0.07)


def _flash_banner(term: Terminal, new_owner: str | None) -> None:
    """Casino-style 'CAPTURED!' banner with a whoosh sound, rendered as
    block-letter ASCII art via `_show_banner`."""
    owner_color = _GREEN if new_owner == Player.PLAYER else _RED
    play_capture_banner()
    _show_banner(term, _BANNER_WORD, owner_color)


def show_victory_banner(term: Terminal | None) -> None:
    """ASCII-art 'YOU WIN!' banner for a player match win."""
    if term is None or not term.does_styling:
        return
    _show_banner(term, "YOU WIN!", _GREEN)


def show_lose_banner(term: Terminal | None) -> None:
    """ASCII-art 'YOU LOSE!' banner for a match loss."""
    if term is None or not term.does_styling:
        return
    _show_banner(term, "YOU LOSE!", _RED)


def show_draw_banner(term: Terminal | None) -> None:
    """ASCII-art 'DRAW!' banner for a tied match."""
    if term is None or not term.does_styling:
        return
    _show_banner(term, "DRAW!", _YELLOW)


def show_rule_banner(term: Terminal | None, rule_name: str, owner: str | None) -> None:
    """ASCII-art banner announcing a special capture rule (Same, Plus,
    Combo, ...) that triggered beyond the basic value comparison."""
    if term is None or not term.does_styling:
        return
    color = _GREEN if owner == Player.PLAYER else _RED
    _show_banner(term, f"{rule_name.upper()}!", color)


def animate_captures(
    term: Terminal | None,
    cursor_row: int,
    captures: list[tuple[int, Card]],
    new_owner: Player | None,
    col_offset: int = 0,
    events: list[str] | None = None,
) -> None:
    """Flip captured cards in place with a color-flash effect, then apply
    the ownership change and pop up a center-screen ASCII-art "CAPTURED!"
    banner. Falls back to a silent ownership swap when no interactive
    terminal is available.
    """
    if term is None or not term.does_styling or not captures:
        for _, ncard in captures:
            ncard.owner = new_owner
        return

    squeeze = _FLASH + f"{'▐▌':^{CELL_W}}" + _RESET
    thin = _FLASH + f"{'│':^{CELL_W}}" + _RESET

    _paint(term, cursor_row, col_offset, captures, lambda _card, _r: squeeze)
    time.sleep(0.22)

    _paint(term, cursor_row, col_offset, captures, lambda _card, _r: thin)
    time.sleep(0.18)

    for _, ncard in captures:
        ncard.owner = new_owner

    _paint(
        term, cursor_row, col_offset, captures, lambda card, r: _ROW_RENDERERS[r](card)
    )
    time.sleep(0.2)

    if new_owner == Player.PLAYER:
        show_capture_particles(term, cursor_row, captures, col_offset)

    for rule_name in events or ():
        show_rule_banner(term, rule_name, new_owner)

    _flash_banner(term, new_owner)
