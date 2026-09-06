from __future__ import annotations

import contextlib
import re
from typing import TYPE_CHECKING

from ..models.card import Card
from .color import Color
from .render import CELL_W, render_row1, render_row2, render_row3, render_row4

if TYPE_CHECKING:
    from blessed import Terminal

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _visible_len(text: str) -> int:
    """Visible length without ANSI escape codes."""
    return len(_ANSI_RE.sub("", text))


def _card_box(
    card: Card | None,
    show: bool,
    is_highlight: bool,
    term: Terminal | None,
) -> list[str]:
    """Build a 6-line boxed card using arrow sprites like the board.

    Layout (CELL_W=18, BOX_W=20):
        ┌──────────────────┐
        │ ■Name            │  render_row1
        │       ▲ 7        │  render_row2
        │ ◀ 1   Fire   5 ▶ │  render_row3
        │       ▼ 3        │  render_row4
        └──────────────────┘

    When ``show`` is False the inner rows show ``???`` placeholders.
    When ``is_highlight`` the borders use the highlight colour and,
    if a styled ``term`` is available, the whole box is wrapped with
    ``term.bold_black_on_cyan`` (same inverted-bar style as the menus).
    Returns list of 6 strings (already coloured).
    """
    w = CELL_W
    if is_highlight:
        top = Color.highlight("┌" + "─" * w + "┐")
        bot = Color.highlight("└" + "─" * w + "┘")
        side_hl = Color.highlight("│")
    else:
        top = Color.border("┌" + "─" * w + "┐")
        bot = Color.border("└" + "─" * w + "┘")
        side_hl = Color.border("│")

    if show and card is not None:
        r1 = render_row1(card)
        r2 = render_row2(card)
        r3 = render_row3(card)
        r4 = render_row4(card)
    else:
        r1 = " " * w
        r2 = " " * w
        plain = f"{'???':^{w}}"
        r3 = plain
        r4 = " " * w

    lines = [
        top,
        f"{side_hl}{r1}{side_hl}",
        f"{side_hl}{r2}{side_hl}",
        f"{side_hl}{r3}{side_hl}",
        f"{side_hl}{r4}{side_hl}",
        bot,
    ]

    if is_highlight and term is not None and hasattr(term, "bold_black_on_cyan"):
        with contextlib.suppress(Exception):
            lines = [term.bold_black_on_cyan(line) for line in lines]
    return lines


def display_hand(
    hand: list[Card],
    label: str,
    show: bool = True,
    term: Terminal | None = None,
    highlight: int | None = None,
) -> None:
    """Print a hand using boxed arrow-sprite cards like the board.

    Each card is rendered as a mini board cell:
        ┌──────────────────┐
        │ ■Geezard         │
        │       ▲ 1        │
        │ ◀ 1        5 ▶   │
        │       ▼ 4        │
        └──────────────────┘
      Lv:1    (level line below)

    Cards are laid out horizontally (one row of boxes) so the block stays
    compact on screen — matching the board's ``▲ ◀ ▶ ▼`` notation instead
    of the old ``T: R: B: L:`` text. ``highlight`` draws that card's box
    with the inverted-bar style (and yellow borders) used by the menus.
    When ``term`` is a styled terminal the whole block is horizontally
    centred; otherwise it prints left-aligned. ``show=False`` renders
    face-down ``???`` boxes.
    """
    box_w = CELL_W + 2
    gap = 1

    header = f"  {label}'s Hand:"
    boxes: list[list[str]] = []
    for idx, card in enumerate(hand):
        is_hl = highlight is not None and idx == highlight
        c: Card | None = card if show else None
        boxes.append(_card_box(c, show, is_hl, term))

    lines: list[str] = []
    lines.append(header)

    if not hand:
        sep = "  " + "─" * 60
        lines.append(sep)
        lines.append(sep)
    else:
        n = len(hand)
        block_w = n * box_w + (n - 1) * gap
        top_sep = "  " + "─" * block_w
        lines.append(top_sep)

        index_parts: list[str] = []
        for idx in range(n):
            is_hl = highlight is not None and idx == highlight
            txt = f"[{idx + 1}]"
            plain = f"{txt:^{box_w}}"
            if is_hl and term is not None and hasattr(term, "bold_black_on_cyan"):
                with contextlib.suppress(Exception):
                    plain = term.bold_black_on_cyan(plain)
            index_parts.append(plain)
        index_line = "  " + (" " * gap).join(index_parts)
        lines.append(index_line)

        for row in range(6):
            parts = [boxes[col][row] for col in range(n)]
            combined = (" " * gap).join(parts)
            lines.append("  " + combined)

        lvl_parts: list[str] = []
        for _idx, card in enumerate(hand):
            txt = f"Lv:{card.level}" if show else "???"
            plain = f"{txt:^{box_w}}"
            lvl_parts.append(plain)
        lvl_line = "  " + (" " * gap).join(lvl_parts)
        lines.append(lvl_line)

        bot_sep = "  " + "─" * block_w
        lines.append(bot_sep)

    visible_max = max(_visible_len(ln) for ln in lines) if lines else 0
    pad = 0
    if term is not None and term.does_styling:
        pad = max(0, (term.width - visible_max) // 2)

    print()
    for line in lines:
        out = " " * pad + line
        print(out)


def print_banner() -> None:
    print("""
 ╔══════════════════════════════════════════════════════════╗
 ║          TRIPLE TRIAD  —  Final Fantasy VIII             ║
 ║                       Text Edition  🃏                   ║
 ╚══════════════════════════════════════════════════════════╝
   """)


def print_help() -> None:
    print("""
  ╔══════════════════════════════════════════════════════════╗
  ║              TRIPLE TRIAD - HOW TO PLAY                  ║
  ╚══════════════════════════════════════════════════════════╝

  OBJECTIVE
  ─────────
  Capture more cards than your opponent on a 3×3 grid.
  Each player starts with 5 cards. The game ends when all
  9 grid spaces are filled.

  CARD ANATOMY
  ────────────
  Each card has 4 directional values (1-10, shown as A for 10) and optionally
  an element:

         ▲ Top
         │
  ◀ Left ┼ Right ▶
         │
         ▼ Bottom

  Example: Ifrit [Fire] ▲9 ▶8 ▼6 ◀5
    - Top: 9, Right: 8, Bottom: 6, Left: 5
    - Element: Fire (can affect gameplay with certain rules)

  BASIC GAMEPLAY
  ──────────────
  1. Players take turns placing one card on an empty space.
  2. When a card is placed adjacent to an opponent's card,
     compare the touching values:
       - Your card's value vs opponent's touching value
       - Higher value WINS and captures the opponent's card
  3. Captured cards change ownership (color/indicator).
  4. Game ends when all 9 spaces are filled.
  5. Player with most cards wins!

  ELEMENT SQUARES
  ───────────────
  Some boards have elemental squares. When you place a card on
  a square matching its element, all directional values receive
  a +1 bonus during capture comparisons:
    - Card element matches square element → +1 to all sides
    - Bonus is temporary, only active during comparisons
    - Elements shown on empty cells as abbreviations (e.g. [1]🔥)

  CAPTURE EXAMPLE
  ───────────────
  Your card (Right=8) placed next to opponent's card (Left=5):
    - Your 8 > Opponent's 5 → You capture their card!

  If your card's value is LOWER or EQUAL, no capture occurs
  (unless Same/Plus rules are active).

  OPTIONAL RULES
  ──────────────
  Open:   CPU's hand is visible to you
  Same:   If 2+ adjacent cards share equal values, ALL are
          captured by the placed card
  Plus:   If 2+ adjacent cards share equal value SUMS, ALL
          are captured
  Random: Cards are dealt randomly from the full card pool

  DECK SELECTION
  ──────────────
  Before each game, choose your 5 cards:
    [1] Browse all 110 cards and pick manually
    [2] Random starter deck (low-level cards)
    [3] Random deck (any level)
    [4] Preset themed decks
    [5] Load a saved deck

  SAVED DECKS (SHELF)
  ───────────────────
  After picking cards manually (option 1), you can save
  your deck to a local shelf file for reuse. Saved decks
  are stored in:
    Linux:   ~/.local/share/triple-triad/decks.json
    macOS:   ~/Library/Application Support/triple-triad/decks.json
    Windows: %APPDATA%/triple-triad/decks.json

  DURING YOUR TURN
  ────────────────
  - Enter a card number from your hand (1-5) to select it
  - Then use the arrow keys (↑ ↓ ← →) to move the yellow
     border marker to an empty cell, and press Enter to place
  - Press Escape or 'r' to go back and pick another card
  - Press 'q' at any prompt to quit back to the main menu
  - In plain terminals (no arrow keys), you can still enter
     the cell number (1-9) directly
  - Strategy matters: position cards to maximize captures!

  ╔═════════════════════════════════════╗
  ║              Good luck!             ║
  ╚═════════════════════════════════════╝
  """)
