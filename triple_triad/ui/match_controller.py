"""Input controllers for the match screens.

Translates keyboard input into a (card, position) move, driving the
redraw callbacks. Raises ``QuitGameError`` when the player quits.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..constants import BOARD_CELLS
from ..models.board import Board
from ..models.card import Card
from .card_selector import select_card
from .display import display_hand
from .match_view import draw_key_hints, hand_block_lines, render_turn_screen
from .position_selector import QuitGameError, select_position

if TYPE_CHECKING:
    from blessed import Terminal


@dataclass
class TurnContext:
    """Everything the interactive move selector needs to draw one turn."""

    board: Board
    player_hand: list[Card]
    other_hand: list[Card]
    other_label: str
    rules: Collection[str]
    term: Terminal | None
    use_screen: bool
    turn_label: str
    turn_number: int
    p_score: int
    c_score: int
    score_labels: tuple[str, str] = ("You", "CPU")
    sep: str = "═"


def get_local_move(ctx: TurnContext) -> tuple[Card, int]:
    """Prompt the local player for a card and a board position.

    Works in both fullscreen (arrow-key selectors) and plain-line (numbered
    prompts) modes. Returns the chosen card (still in the hand — the caller
    pops it) and the target position.
    """
    show_other = "Open" in ctx.rules
    extra = hand_block_lines(len(ctx.player_hand)) + hand_block_lines(len(ctx.other_hand))

    def _redraw(highlight: int | None = None, card_hl: int | None = None) -> None:
        render_turn_screen(
            ctx.term,
            ctx.use_screen,
            ctx.board,
            ctx.turn_label,
            ctx.turn_number,
            ctx.p_score,
            ctx.c_score,
            score_labels=ctx.score_labels,
            sep=ctx.sep,
            extra_lines=extra,
            highlight=highlight,
        )
        display_hand(ctx.player_hand, "Your", term=ctx.term, highlight=card_hl)
        display_hand(ctx.other_hand, ctx.other_label, show=show_other, term=ctx.term)
        draw_key_hints(ctx.term, ctx.use_screen)

    display_hand(ctx.player_hand, "Your", term=ctx.term)
    display_hand(ctx.other_hand, ctx.other_label, show=show_other, term=ctx.term)
    draw_key_hints(ctx.term, ctx.use_screen)

    while True:
        if ctx.term is not None and ctx.use_screen:
            ci = select_card(
                ctx.player_hand, ctx.term, ctx.use_screen, lambda h: _redraw(card_hl=h)
            )
            if ci is None:
                _redraw()
                continue
        else:
            while True:
                raw = input(
                    f"\n  Choose card (1-{len(ctx.player_hand)}) [r=redraw, q=quit]: "
                )
                if raw.strip().lower() == "q":
                    raise QuitGameError
                if raw.strip().lower() == "r":
                    _redraw()
                    continue
                try:
                    ci = int(raw) - 1
                    if 0 <= ci < len(ctx.player_hand):
                        break
                    print(f"  ✗ Enter a number between 1 and {len(ctx.player_hand)}.")
                except ValueError:
                    print("  ✗ Enter a number.")

        if ctx.term is not None and ctx.use_screen:
            pos = select_position(
                ctx.board,
                ctx.term,
                ctx.use_screen,
                lambda h: _redraw(highlight=h),
            )
            if pos is None:
                _redraw()
                continue
        else:
            empty = [i for i in range(BOARD_CELLS) if ctx.board.is_empty(i)]
            while True:
                raw = input(
                    f"  Choose position (1-{BOARD_CELLS}) [r=redraw, q=quit]: "
                )
                if raw.strip().lower() == "q":
                    raise QuitGameError
                if raw.strip().lower() == "r":
                    _redraw()
                    continue
                try:
                    pos = int(raw) - 1
                    if pos in empty:
                        break
                    print("  ✗ Position taken or invalid.")
                except ValueError:
                    print("  ✗ Enter a number.")

        return ctx.player_hand[ci], pos
