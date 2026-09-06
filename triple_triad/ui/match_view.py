"""Rendering helpers for the match screens (turn view, game over, banners).

This module is pure presentation: it draws and sleeps, but never mutates
game state. The engine's game loop calls into it.
"""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING

from ..models.board import Board
from ..models.player import MatchResult, Player
from ..synth.sfx import play_defeat_theme, play_victory_fanfare
from ..ui.capture_fx import (
    show_draw_banner,
    show_lose_banner,
    show_victory_banner,
)
from ..ui.cli import pause_message
from .render import board_total_width, render_board

if TYPE_CHECKING:
    from blessed import Terminal


def decide_first(term: Terminal | None) -> Player:
    """Animate a bouncing selector between YOU and CPU, then reveal who goes
    first. Draws within the caller's already-active fullscreen session
    (pass None to skip the animation and just pick randomly).
    """
    if term is None:
        return random.choice([Player.PLAYER, Player.CPU])
    first = random.choice([Player.PLAYER, Player.CPU])
    winner = 0 if first == Player.PLAYER else 1

    cur = random.randint(0, 1)
    seq: list[int] = []
    for _ in range(random.randint(4, 7)):
        seq.append(cur)
        cur = 1 - cur
    seq.append(winner)

    labels = ["  YOU  ", "  CPU  "]
    gap = 8
    total_w = len(labels[0]) + gap + len(labels[1])
    base_x = max(0, (term.width - total_w) // 2)
    cpu_x = base_x + len(labels[0]) + gap
    arrow_offset = len(labels[0]) // 2
    positions = (base_x, cpu_x)

    with term.cbreak(), term.hidden_cursor():
        print(term.clear + term.normal, end="")
        title = "Who goes first?"
        print(
            term.move_yx(5, max(0, (term.width - len(title)) // 2))
            + term.bold_cyan(title),
            end="",
            flush=True,
        )

        for idx, label in enumerate(labels):
            print(term.move_yx(8, positions[idx]) + term.bold_white(label), end="")

        for i, sel in enumerate(seq):
            progress = i / max(1, len(seq) - 1)
            delay = 0.1 + progress * 0.3

            out = []
            for idx, x in enumerate(positions):
                glyph = term.yellow("▲") if idx == sel else " "
                out.append(term.move_yx(9, x + arrow_offset) + glyph)

            print("".join(out), end="", flush=True)
            time.sleep(delay)

        print(
            term.move_yx(8, positions[winner])
            + term.bold_black_on_cyan(labels[winner]),
            end="",
            flush=True,
        )

        result = "You go first!" if first == Player.PLAYER else "CPU goes first!"
        print(
            term.move_yx(11, max(0, (term.width - len(result)) // 2))
            + term.bold_yellow(result),
            end="",
            flush=True,
        )
        time.sleep(1)

    return first


def hand_block_lines(hand_size: int) -> int:
    """Line count of one ``display_hand`` call with boxed arrow sprites.

    Boxed layout (horizontal row of boxes):
        blank + header + top_sep + index_row + 6 box rows + level_row + bot_sep
        = 11 lines + blank = 12 total when hand non-empty.
    Empty hand: blank + header + sep + sep = 4.
    """
    if hand_size <= 0:
        return 4
    return 12


def draw_key_hints(term: Terminal | None, use_screen: bool = True) -> None:
    """Draw the 'r: redraw screen | q: exit main menu' hint at the bottom
    center of the screen. No-op when not on a styled terminal."""
    if not use_screen or term is None:
        return
    hint = "  r: redraw screen   |   q: exit main menu  "
    hint_x = max(0, (term.width - len(hint)) // 2)
    print(
        term.move_yx(term.height - 1, hint_x) + term.dim(hint),
        end="",
        flush=True,
    )


def render_turn_screen(
    term: Terminal | None,
    use_screen: bool,
    board: Board,
    turn_label: str,
    turn_number: int,
    p_score: int,
    c_score: int,
    score_labels: tuple[str, str] = ("You", "CPU"),
    sep: str = "═",
    note: str | None = None,
    extra_lines: int = 0,
    highlight: int | None = None,
) -> tuple[int, int]:
    """Draw one turn's screen — clearing first if a persistent (fullscreen)
    terminal is in use, so the board updates in place instead of scrolling.
    Padded with blank lines on top so the block sits vertically centered in
    the terminal; ``extra_lines`` should count whatever the caller prints
    immediately after this returns (e.g. hand listings), so the padding
    accounts for the full block, not just the header/board/score. Header,
    score, and note lines are each centered horizontally on their own; the
    board is centered as a whole block (every row shares one left offset so
    its grid lines stay aligned).

    Returns ``(cursor_row, col_offset)``: ``cursor_row`` is the number of
    lines from the board's top border down to the resulting (blank) cursor
    line, and ``col_offset`` is how many columns the board was shifted
    right — both are what capture_fx needs to place its flip animation.
    """
    if use_screen and term is not None:
        print(term.clear, end="")

    def _center(text: str) -> str:
        if not (use_screen and term is not None):
            return text
        hpad = max(0, (term.width - len(text)) // 2)
        return " " * hpad + text

    bar = sep * 62
    board_text = render_board(board, highlight=highlight)
    own_lines = 6 + board_text.count("\n") + 1 + (2 if note is not None else 0)
    vpad = 0
    col_offset = 0
    if use_screen and term is not None:
        vpad = max(0, (term.height - (own_lines + extra_lines)) // 2)
        print("\n" * vpad, end="")
        col_offset = max(0, (term.width - board_total_width()) // 2)

    print()
    print(_center(bar))
    print(_center(f"  Turn {turn_number}  |  {turn_label}"))
    print(_center(bar))
    if col_offset:
        board_text = "\n".join(
            " " * col_offset + line for line in board_text.split("\n")
        )
    print(board_text)
    you_label, opp_label = score_labels
    print()
    print(_center(f"  Score — {you_label}: {p_score}  {opp_label}: {c_score}"))
    lines = board_text.count("\n") + 1 + 2
    if note is not None:
        print()
        print(_center(f"  {note}"))
        lines += 2

    if use_screen and term is not None:
        draw_key_hints(term)
        print(term.move_yx(vpad + 4 + lines, 0), end="", flush=True)

    return lines, col_offset


def render_game_over_screen(
    term: Terminal | None,
    use_screen: bool,
    board: Board,
    p_score: int,
    c_score: int,
    score_labels: tuple[str, str] = ("You", "CPU"),
    sep: str = "═",
    result_text: str | None = None,
) -> None:
    """Draw the final board, score, and win/lose/draw result, centered the
    same way ``render_turn_screen`` centers every other screen in the
    game."""
    if use_screen and term is not None:
        print(term.clear, end="")

    def _center(text: str) -> str:
        if not (use_screen and term is not None):
            return text
        hpad = max(0, (term.width - len(text)) // 2)
        return " " * hpad + text

    bar = sep * 62
    board_text = render_board(board)
    own_lines = 6 + board_text.count("\n") + 1 + (2 if result_text is not None else 0)
    col_offset = 0
    if use_screen and term is not None:
        vpad = max(0, (term.height - own_lines) // 2)
        print("\n" * vpad, end="")
        col_offset = max(0, (term.width - board_total_width()) // 2)

    print()
    print(_center(bar))
    print(_center("  GAME OVER"))
    print(_center(bar))
    if col_offset:
        board_text = "\n".join(
            " " * col_offset + line for line in board_text.split("\n")
        )
    print(board_text)
    you_label, opp_label = score_labels
    print()
    print(_center(f"  Final Score — {you_label}: {p_score}  {opp_label}: {c_score}"))
    if result_text is not None:
        print()
        print(_center(f"  {result_text}"))


def show_match_outcome(
    term: Terminal | None,
    use_screen: bool,
    board: Board,
    p_final: int,
    c_final: int,
    result_text: str,
    outcome: MatchResult,
    score_labels: tuple[str, str] = ("You", "CPU"),
) -> None:
    """Play the win/lose/draw fanfare, show the matching banner, redraw the
    final screen, and wait for the player. Shared by the single-player and
    P2P game loops."""
    banner = None
    if outcome == MatchResult.P1_WIN:
        play_victory_fanfare()
        banner = show_victory_banner
    elif outcome == MatchResult.P2_WIN:
        play_defeat_theme()
        banner = show_lose_banner
    else:
        banner = show_draw_banner

    if use_screen and term is not None:
        banner(term)
        render_game_over_screen(
            term,
            use_screen,
            board,
            p_final,
            c_final,
            score_labels=score_labels,
            result_text=result_text,
        )
    pause_message()
