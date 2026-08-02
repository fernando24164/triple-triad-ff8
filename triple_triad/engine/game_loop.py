from __future__ import annotations

import random
import time
from collections.abc import Collection, Iterator
from contextlib import contextmanager, nullcontext
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from blessed import Terminal

    from ..synth.player import ChiptunePlayer

from ..ai.base import cpu_choose
from ..constants import BOARD_CELLS
from ..data.cards import Element
from ..models.board import Board
from ..models.card import Card
from ..network.connection import P2PConnection
from ..network.protocol import (
    MOVE_TIMEOUT_S,
    MessageType,
    make_disconnect,
    make_forfeit,
    make_move,
    parse_packet,
)
from ..synth.sfx import (
    play_cancel,
    play_capture_lose,
    play_capture_win,
    play_defeat_theme,
    play_victory_fanfare,
)
from ..synth.wave_generators import generate_boogie_buffer, generate_music_buffer
from ..ui.capture_fx import (
    animate_captures,
    show_draw_banner,
    show_lose_banner,
    show_victory_banner,
)
from ..ui.card_selector import select_card
from ..ui.cli import pause_message
from ..ui.display import display_hand
from ..ui.position_selector import QuitGameError, select_position
from .rules import resolve_captures
from .scoring import calculate_final_scores, calculate_scores

try:
    from blessed import Terminal as _BlessedTerminal

    _HAS_TERMINAL = True
except Exception:
    _BlessedTerminal = None  # type: ignore[misc, assignment]
    _HAS_TERMINAL = False


def _get_terminal() -> Terminal | None:
    """Return a blessed Terminal instance if available, else None."""
    if not _HAS_TERMINAL or _BlessedTerminal is None:
        return None
    try:
        return _BlessedTerminal()
    except Exception:
        return None


@contextmanager
def _boogie_during_match(music_player: ChiptunePlayer | None) -> Iterator[None]:
    """Swap the main menu music for the gameplay 'boogie' theme while cards
    are being played, then swap back to the menu theme — however the block
    exits (normal return, early return, or exception). A no-op when
    there's no shared player (headless mode, tests)."""
    if music_player is None:
        yield
        return
    music_player.switch_track(generate_boogie_buffer)
    try:
        yield
    finally:
        music_player.switch_track(generate_music_buffer)


def _decide_first(term: Terminal | None) -> str:
    """Animate a bouncing selector between YOU and CPU, then reveal who goes
    first. Draws within the caller's already-active fullscreen session
    (pass None to skip the animation and just pick randomly)."""
    if term is None:
        return random.choice(["P", "CPU"])
    first = random.choice(["P", "CPU"])
    winner = 0 if first == "P" else 1

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
        # Clear and draw the static title once — clearing every frame in
        # the loop below is what caused the whole screen to flash/blink.
        print(term.clear + term.normal, end="")
        title = "Who goes first?"
        print(
            term.move_yx(5, max(0, (term.width - len(title)) // 2))
            + term.bold_cyan(title),
            end="",
            flush=True,
        )

        # The labels never change appearance during the bounce — only the
        # arrow below moves — so draw them once. Toggling a background
        # color on and off every frame (as fast as 40ms early on) is what
        # read as strobing rather than motion.
        for idx, label in enumerate(labels):
            print(term.move_yx(8, positions[idx]) + term.bold_white(label), end="")

        for i, sel in enumerate(seq):
            progress = i / max(1, len(seq) - 1)
            delay = 0.1 + progress * 0.3  # kept slow enough to read as a hop

            out = []
            # Overwrite both possible arrow slots every frame — a blank at
            # the unselected one, the arrow at the selected one — so the
            # old arrow never lingers without needing a full clear.
            for idx, x in enumerate(positions):
                glyph = term.yellow("▲") if idx == sel else " "
                out.append(term.move_yx(9, x + arrow_offset) + glyph)

            print("".join(out), end="", flush=True)
            time.sleep(delay)

        # Reveal: highlight the winning side once, as the payoff.
        print(
            term.move_yx(8, positions[winner])
            + term.bold_black_on_cyan(labels[winner]),
            end="",
            flush=True,
        )

        result = "You go first!" if first == "P" else "CPU goes first!"
        print(
            term.move_yx(11, max(0, (term.width - len(result)) // 2))
            + term.bold_yellow(result),
            end="",
            flush=True,
        )
        time.sleep(1)

    return first


def _hand_block_lines(hand_size: int) -> int:
    """Line count of one ``display_hand`` call: blank+label, separator,
    one line per card, separator."""
    return hand_size + 4


def _render_turn_screen(
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
    board_text = board.display(highlight=highlight)
    own_lines = 6 + board_text.count("\n") + 1 + (2 if note is not None else 0)
    col_offset = 0
    if use_screen and term is not None:
        vpad = max(0, (term.height - (own_lines + extra_lines)) // 2)
        print("\n" * vpad, end="")
        col_offset = max(0, (term.width - Board.total_width()) // 2)

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
    return lines, col_offset


def _render_game_over_screen(
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
    same way ``_render_turn_screen`` centers every other screen in the
    game."""
    if use_screen and term is not None:
        print(term.clear, end="")

    def _center(text: str) -> str:
        if not (use_screen and term is not None):
            return text
        hpad = max(0, (term.width - len(text)) // 2)
        return " " * hpad + text

    bar = sep * 62
    board_text = board.display()
    own_lines = 6 + board_text.count("\n") + 1 + (2 if result_text is not None else 0)
    col_offset = 0
    if use_screen and term is not None:
        vpad = max(0, (term.height - own_lines) // 2)
        print("\n" * vpad, end="")
        col_offset = max(0, (term.width - Board.total_width()) // 2)

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


def run_game(
    player_hand: list[Card],
    cpu_hand: list[Card],
    rules: Collection[str],
    ai_mode: str,
    board_elements: list[Element | None] | None = None,
    ai_randomness: float = 0.0,
    music_player: ChiptunePlayer | None = None,
) -> str:
    """Run the full game loop until the board is full."""
    board = Board(elements=board_elements)
    term = _get_terminal()
    use_screen = term is not None and term.does_styling

    screen = term.fullscreen() if (use_screen and term is not None) else nullcontext()
    with screen, _boogie_during_match(music_player):
        first = _decide_first(term if use_screen else None)

        turn = first
        turn_number = 1

        while any(board.is_empty(i) for i in range(BOARD_CELLS)):
            p_score, c_score = calculate_scores(board, player_hand, cpu_hand)
            turn_label = "YOUR TURN" if turn == "P" else "CPU TURN"
            choose_extra = (
                _hand_block_lines(len(player_hand)) + _hand_block_lines(len(cpu_hand))
                if turn == "P"
                else 2  # "\n  CPU is thinking..."
            )
            _render_turn_screen(
                term,
                use_screen,
                board,
                turn_label,
                turn_number,
                p_score,
                c_score,
                extra_lines=choose_extra,
            )

            if turn == "P":
                try:
                    show_cpu = "Open" in rules
                    display_hand(player_hand, "Your", term=term)
                    display_hand(cpu_hand, "CPU", show=show_cpu, term=term)

                    def _redraw(
                        turn_label: str = turn_label,
                        turn_number: int = turn_number,
                        p_score: int = p_score,
                        c_score: int = c_score,
                        show_cpu: bool = show_cpu,
                        extra: int = choose_extra,
                        highlight: int | None = None,
                        card_hl: int | None = None,
                    ) -> None:
                        _render_turn_screen(
                            term,
                            use_screen,
                            board,
                            turn_label,
                            turn_number,
                            p_score,
                            c_score,
                            extra_lines=extra,
                            highlight=highlight,
                        )
                        display_hand(player_hand, "Your", term=term, highlight=card_hl)
                        display_hand(cpu_hand, "CPU", show=show_cpu, term=term)

                    if use_screen and term is not None:
                        ci = select_card(
                            player_hand, term, use_screen, lambda h: _redraw(card_hl=h)
                        )
                        if ci is None:
                            _redraw()
                            continue
                    else:
                        while True:
                            raw = input(
                                f"\n  Choose card (1-{len(player_hand)}) [r=redraw, q=quit]: "
                            )
                            if raw.strip().lower() == "q":
                                raise QuitGameError
                            if raw.strip().lower() == "r":
                                _redraw()
                                continue
                            try:
                                ci = int(raw) - 1
                                if 0 <= ci < len(player_hand):
                                    break
                                print(
                                    f"  ✗ Enter a number between 1 and {len(player_hand)}."
                                )
                            except ValueError:
                                print("  ✗ Enter a number.")

                    if use_screen and term is not None:
                        pos = select_position(
                            board,
                            term,
                            use_screen,
                            lambda h: _redraw(highlight=h),
                        )
                        if pos is None:
                            _redraw()
                            continue
                    else:
                        empty = [i for i in range(BOARD_CELLS) if board.is_empty(i)]
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

                    card = player_hand.pop(ci)
                    card.owner = "P"
                    board.place(pos, card)
                    move_note = f"You placed [{card.name}] at position {pos + 1}"
                except QuitGameError:
                    play_cancel()
                    return "quit"

            else:
                print("\n  CPU is thinking...")
                if use_screen:
                    # The AI move is computed instantly, so without this
                    # pause the "CPU TURN" screen would flash off again
                    # before it's even visible — this also gives the
                    # "thinking" message a moment to actually be read.
                    time.sleep(0.5)
                ci, cpu_pos = cpu_choose(
                    board, cpu_hand, rules, mode=ai_mode, randomness=ai_randomness
                )
                assert cpu_pos is not None, "CPU had no valid move on a non-full board"
                card = cpu_hand.pop(ci)
                card.owner = "CPU"
                board.place(cpu_pos, card)
                pos = cpu_pos
                move_note = f"CPU placed [{card.name}] at position {pos + 1}"

            captures, events = resolve_captures(board, pos, card, rules)

            # Redraw cleanly with the placed card visible (pre-capture) —
            # this becomes the animation's anchor.
            cursor_row, col_offset = _render_turn_screen(
                term,
                use_screen,
                board,
                turn_label,
                turn_number,
                p_score,
                c_score,
                note=move_note,
            )

            if captures:
                old_owners = {cpos: ccard.owner for cpos, ccard in captures}
                if use_screen:
                    animate_captures(
                        term, cursor_row, captures, card.owner, col_offset, events
                    )
                    # Wipe the "CAPTURED!" banner left behind by the animation.
                    _render_turn_screen(
                        term,
                        use_screen,
                        board,
                        turn_label,
                        turn_number,
                        p_score,
                        c_score,
                        note=move_note,
                    )
                else:
                    for _, ccard in captures:
                        ccard.owner = card.owner
                play_capture_win() if card.owner == "P" else play_capture_lose()
            if not use_screen:
                # In screen mode this is already announced by the ASCII
                # rule banner(s) animate_captures just showed.
                for evt in events:
                    print(f"  *** {evt.upper()}! ***")
            for cap_pos, ncard in captures:
                old_owner = old_owners[cap_pos]
                ncard.owner = card.owner
                attacker_label = "You" if card.owner == "P" else "CPU"
                defender_label = "CPU" if old_owner == "CPU" else "You"
                print(
                    f"  ⚔  [{card.name}] captured [{ncard.name}]! "
                    f"({defender_label} → {attacker_label})"
                )

            if use_screen:
                time.sleep(0.9)

            turn = "CPU" if turn == "P" else "P"
            turn_number += 1

        p_final, c_final = calculate_final_scores(board)

        if p_final > c_final:
            result_text = "🏆  YOU WIN!  Congratulations!"
        elif c_final > p_final:
            result_text = "💀  CPU WINS!  Better luck next time!"
        else:
            result_text = "🤝  IT'S A DRAW!"

        _render_game_over_screen(
            term, use_screen, board, p_final, c_final, result_text=result_text
        )

        if p_final > c_final:
            play_victory_fanfare()
            if use_screen:
                show_victory_banner(term)
                _render_game_over_screen(
                    term, use_screen, board, p_final, c_final, result_text=result_text
                )
            pause_message()
            return "P"
        elif c_final > p_final:
            play_defeat_theme()
            if use_screen:
                show_lose_banner(term)
                _render_game_over_screen(
                    term, use_screen, board, p_final, c_final, result_text=result_text
                )
            pause_message()
            return "CPU"
        else:
            if use_screen:
                show_draw_banner(term)
                _render_game_over_screen(
                    term, use_screen, board, p_final, c_final, result_text=result_text
                )
            pause_message()
            return "Draw"


# ── P2P Game Loop ────────────────────────────────────────────────────────────


def run_p2p_game(
    conn: P2PConnection,
    player_hand: list[Card],
    opponent_hand: list[Card],
    rules: Collection[str],
    board_elements: list[Element | None] | None,
    local_role: str,
    first_turn: str,
    headless: bool = False,
    music_player: ChiptunePlayer | None = None,
) -> str:
    """Run a P2P multiplayer game loop.

    Args:
        conn: Active P2P connection to the opponent.
        player_hand: Local player's hand (cards with owner='P').
        opponent_hand: Remote opponent's hand (cards with owner='CPU').
        rules: Active rules set.
        board_elements: Board element configuration.
        local_role: 'P1' or 'P2' - this client's role.
        first_turn: 'P' or 'CPU' - who goes first.
        headless: If True, use AI for all local moves.
        music_player: Shared menu music player to duck while the match
            plays and restore afterward, or None to skip music switching.

    Returns:
        'P1_WIN', 'P2_WIN', or 'DRAW'.
    """
    board = Board(elements=board_elements)
    turn = first_turn
    turn_number = 1
    term = _get_terminal() if not headless else None
    use_screen = not headless and term is not None and term.does_styling
    score_labels = ("You", "Opponent")

    screen = term.fullscreen() if (use_screen and term is not None) else nullcontext()
    with screen, _boogie_during_match(music_player if not headless else None):
        while any(board.is_empty(i) for i in range(BOARD_CELLS)):
            p_score, c_score = calculate_scores(board, player_hand, opponent_hand)
            turn_label = "YOUR TURN" if turn == "P" else "OPPONENT TURN"

            is_local_turn = (turn == "P" and local_role == "P1") or (
                turn == "CPU" and local_role == "P2"
            )
            hands_extra = _hand_block_lines(len(player_hand)) + _hand_block_lines(
                len(opponent_hand)
            )
            choose_extra = hands_extra if is_local_turn else hands_extra + 2

            if not headless and term:
                _render_turn_screen(
                    term,
                    use_screen,
                    board,
                    turn_label,
                    turn_number,
                    p_score,
                    c_score,
                    score_labels=score_labels,
                    sep="=",
                    extra_lines=choose_extra,
                )

            pos = -1
            card = None
            move_note = ""

            if is_local_turn:
                if headless:
                    ci, cpu_pos = cpu_choose(board, player_hand, rules, mode="greedy")
                    assert cpu_pos is not None
                    pos = cpu_pos
                    card = player_hand.pop(ci)
                    card.owner = "P"
                    board.place(pos, card)
                    conn.send(make_move(ci, pos))
                else:
                    try:
                        card, pos = _get_local_move_interactive(
                            board,
                            player_hand,
                            opponent_hand,
                            rules,
                            term,
                            local_role,
                            use_screen,
                            turn_label,
                            turn_number,
                            p_score,
                            c_score,
                            score_labels,
                        )
                    except QuitGameError:
                        conn.send(make_forfeit("Player quit"))
                        play_cancel()
                        return "quit"
                    ci_index = player_hand.index(card)
                    player_hand.pop(ci_index)
                    card.owner = "P"
                    board.place(pos, card)
                    conn.send(make_move(ci_index, pos))
                move_note = f"You placed [{card.name}] at position {pos + 1}"
            else:
                if not headless and term:
                    print("\n  Opponent is thinking...")
                    display_hand(player_hand, "Your", show="Open" in rules, term=term)
                    display_hand(opponent_hand, "Opponent", show=True, term=term)

                packet = _wait_for_move(conn, term, headless)
                if packet is None:
                    if not headless and term:
                        print("\n  Opponent took too long!")
                    return "P1_WIN" if local_role == "P1" else "P2_WIN"

                msg_type, payload = parse_packet(packet)
                if msg_type == MessageType.FORFEIT:
                    if not headless and term:
                        reason = payload.get("reason", "")
                        print(f"\n  Opponent forfeited! {reason}")
                    return "P1_WIN" if local_role == "P1" else "P2_WIN"

                if msg_type in (MessageType.DISCONNECT, MessageType.CONNECTION_LOST):
                    if not headless and term:
                        print("\n  Opponent disconnected!")
                    return "P1_WIN" if local_role == "P1" else "P2_WIN"

                opp_ci = payload["card_idx"]
                opp_pos = payload["position"]

                if opp_ci < 0 or opp_ci >= len(opponent_hand):
                    conn.send(make_forfeit("Invalid card index"))
                    return "P1_WIN" if local_role == "P1" else "P2_WIN"

                if opp_pos < 0 or opp_pos >= BOARD_CELLS or not board.is_empty(opp_pos):
                    conn.send(make_forfeit("Invalid position"))
                    return "P1_WIN" if local_role == "P1" else "P2_WIN"

                opp_card = opponent_hand.pop(opp_ci)
                opp_card.owner = "CPU"
                board.place(opp_pos, opp_card)
                card = opp_card
                pos = opp_pos
                move_note = f"Opponent placed [{card.name}] at position {pos + 1}"

            assert card is not None and pos >= 0
            captures, events = resolve_captures(board, pos, card, rules)
            if not headless and term:
                cursor_row, col_offset = _render_turn_screen(
                    term,
                    use_screen,
                    board,
                    turn_label,
                    turn_number,
                    p_score,
                    c_score,
                    score_labels=score_labels,
                    sep="=",
                    note=move_note,
                )
                if captures:
                    old_owners = {cpos: ccard.owner for cpos, ccard in captures}
                    if use_screen:
                        animate_captures(
                            term, cursor_row, captures, card.owner, col_offset, events
                        )
                        # Wipe the "CAPTURED!" banner left behind by the animation.
                        _render_turn_screen(
                            term,
                            use_screen,
                            board,
                            turn_label,
                            turn_number,
                            p_score,
                            c_score,
                            score_labels=score_labels,
                            sep="=",
                            note=move_note,
                        )
                    else:
                        for _, ccard in captures:
                            ccard.owner = card.owner
                    play_capture_win() if card.owner == "P" else play_capture_lose()
                if not use_screen:
                    # In screen mode this is already announced by the ASCII
                    # rule banner(s) animate_captures just showed.
                    for evt in events:
                        print(f"  *** {evt.upper()}! ***")
                for cap_pos, ncard in captures:
                    old_owner = old_owners[cap_pos]
                    ncard.owner = card.owner
                    attacker_label = "You" if card.owner == "P" else "Opponent"
                    defender_label = "Opponent" if old_owner == "CPU" else "You"
                    print(
                        f"  [{card.name}] captured [{ncard.name}]! "
                        f"({defender_label} -> {attacker_label})"
                    )
                if use_screen:
                    time.sleep(0.9)
            else:
                for _, ccard in captures:
                    ccard.owner = card.owner

            turn = "CPU" if turn == "P" else "P"
            turn_number += 1

        p_final, c_final = calculate_final_scores(board)

        if p_final > c_final:
            result = "P1_WIN" if local_role == "P1" else "P2_WIN"
            label = "YOU WIN!"
        elif c_final > p_final:
            result = "P2_WIN" if local_role == "P1" else "P1_WIN"
            label = "You lost. Better luck next time!"
        else:
            result = "DRAW"
            label = "It's a draw!"

        if not headless and term:
            _render_game_over_screen(
                term,
                use_screen,
                board,
                p_final,
                c_final,
                score_labels=("You", "Opponent"),
                result_text=label,
            )

            if label == "YOU WIN!":
                play_victory_fanfare()
                if use_screen:
                    show_victory_banner(term)
                    _render_game_over_screen(
                        term,
                        use_screen,
                        board,
                        p_final,
                        c_final,
                        score_labels=("You", "Opponent"),
                        result_text=label,
                    )
            elif label == "You lost. Better luck next time!":
                play_defeat_theme()
                if use_screen:
                    show_lose_banner(term)
                    _render_game_over_screen(
                        term,
                        use_screen,
                        board,
                        p_final,
                        c_final,
                        score_labels=("You", "Opponent"),
                        result_text=label,
                    )
            elif label == "It's a draw!":
                if use_screen:
                    show_draw_banner(term)
                    _render_game_over_screen(
                        term,
                        use_screen,
                        board,
                        p_final,
                        c_final,
                        score_labels=("You", "Opponent"),
                        result_text=label,
                    )
            pause_message()
        return result


def _get_local_move_interactive(
    board: Board,
    player_hand: list[Card],
    opponent_hand: list[Card],
    rules: Collection[str],
    term: Terminal | None,
    local_role: str,
    use_screen: bool,
    turn_label: str,
    turn_number: int,
    p_score: int,
    c_score: int,
    score_labels: tuple[str, str],
) -> tuple[Card, int]:
    """Get a move from the local player via keyboard input."""
    show_opp = "Open" in rules
    display_hand(player_hand, "Your", term=term)
    display_hand(opponent_hand, "Opponent", show=show_opp, term=term)

    def _redraw(highlight: int | None = None, card_hl: int | None = None) -> None:
        extra = _hand_block_lines(len(player_hand)) + _hand_block_lines(
            len(opponent_hand)
        )
        _render_turn_screen(
            term,
            use_screen,
            board,
            turn_label,
            turn_number,
            p_score,
            c_score,
            score_labels=score_labels,
            sep="=",
            extra_lines=extra,
            highlight=highlight,
        )
        display_hand(player_hand, "Your", term=term, highlight=card_hl)
        display_hand(opponent_hand, "Opponent", show=show_opp, term=term)

    while True:
        if term is not None and use_screen:
            ci = select_card(
                player_hand, term, use_screen, lambda h: _redraw(card_hl=h)
            )
            if ci is None:
                _redraw()
                continue
        else:
            while True:
                raw = input(
                    f"\n  Choose card (1-{len(player_hand)}) [r=redraw, q=quit]: "
                )
                if raw.strip().lower() == "q":
                    raise QuitGameError
                if raw.strip().lower() == "r":
                    _redraw()
                    continue
                try:
                    ci = int(raw) - 1
                    if 0 <= ci < len(player_hand):
                        break
                    print(f"  Enter a number between 1 and {len(player_hand)}.")
                except ValueError:
                    print("  Enter a number.")

        if term is not None and use_screen:
            pos = select_position(
                board,
                term,
                use_screen,
                lambda h: _redraw(highlight=h),
            )
            if pos is None:
                _redraw()
                continue
        else:
            empty = [i for i in range(BOARD_CELLS) if board.is_empty(i)]
            while True:
                raw = input(f"  Choose position (1-{BOARD_CELLS}) [r=redraw, q=quit]: ")
                if raw.strip().lower() == "q":
                    raise QuitGameError
                if raw.strip().lower() == "r":
                    _redraw()
                    continue
                try:
                    pos = int(raw) - 1
                    if pos in empty:
                        break
                    print("  Position taken or invalid.")
                except ValueError:
                    print("  Enter a number.")

        return player_hand[ci], pos


def _wait_for_move(
    conn: P2PConnection,
    term: Terminal | None,
    headless: bool,
) -> dict[str, Any] | None:
    """Block waiting for a MOVE packet from the network, with heartbeat handling.

    Uses queue_get_filtered so non-matching packets (e.g. heartbeats) are
    buffered in ``_pending`` instead of silently discarded.
    """
    start = time.monotonic()
    spinner = [" ", "/", "-", "\\"]
    spin_idx = 0
    expected = {
        MessageType.MOVE,
        MessageType.FORFEIT,
        MessageType.DISCONNECT,
        MessageType.CONNECTION_LOST,
    }

    while time.monotonic() - start < MOVE_TIMEOUT_S:
        packet = conn.queue_get_filtered(expected, timeout=0.3)
        if packet is not None:
            return packet

        if not headless and term:
            elapsed = time.monotonic() - start
            print(
                f"\r  Waiting for opponent... [{spinner[spin_idx]}] ({elapsed:.0f}s)",
                end="",
                flush=True,
            )
            spin_idx = (spin_idx + 1) % len(spinner)

    conn.send(make_disconnect("Timeout"))
    return None


# ── Headless Autoplay P2P Game ───────────────────────────────────────────────


def run_headless_p2p_game(
    conn: P2PConnection,
    player_hand: list[Card],
    opponent_hand: list[Card],
    rules: Collection[str],
    board_elements: list[Element | None] | None,
    local_role: str,
    first_turn: str,
) -> str:
    """Run a headless P2P game using AI for all local moves."""
    return run_p2p_game(
        conn=conn,
        player_hand=player_hand,
        opponent_hand=opponent_hand,
        rules=rules,
        board_elements=board_elements,
        local_role=local_role,
        first_turn=first_turn,
        headless=True,
    )
