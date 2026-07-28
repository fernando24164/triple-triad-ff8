from __future__ import annotations

import random
import time
from collections.abc import Collection
from contextlib import nullcontext
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from blessed import Terminal

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
from ..synth.sfx import play_capture_lose, play_capture_win
from ..ui.capture_fx import animate_captures
from ..ui.cli import pause_message
from ..ui.display import display_hand
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

    with term.cbreak(), term.hidden_cursor():
        for i, sel in enumerate(seq):
            progress = i / max(1, len(seq) - 1)
            delay = 0.04 + progress * 0.35

            out = [term.clear + term.normal]

            title = "Who goes first?"
            out.append(
                term.move_yx(5, max(0, (term.width - len(title)) // 2))
                + term.bold_cyan(title)
            )

            for idx, label in enumerate(labels):
                x = base_x if idx == 0 else cpu_x
                if idx == sel:
                    out.append(term.move_yx(8, x) + term.bold_black_on_cyan(label))
                else:
                    out.append(term.move_yx(8, x) + term.white(label))

            arrow_x = base_x if sel == 0 else cpu_x
            out.append(
                term.move_yx(9, arrow_x + len(labels[sel]) // 2) + term.yellow("▲")
            )

            print("".join(out), end="", flush=True)
            time.sleep(delay)

        result = "You go first!" if first == "P" else "CPU goes first!"
        print(
            term.move_yx(11, max(0, (term.width - len(result)) // 2))
            + term.bold_yellow(result),
            end="",
            flush=True,
        )
        time.sleep(1)

    return first


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
) -> int:
    """Draw one turn's screen — clearing first if a persistent (fullscreen)
    terminal is in use, so the board updates in place instead of scrolling.

    Returns the number of lines from the board's top border down to the
    resulting (blank) cursor line, for use as capture_fx's ``cursor_row``.
    """
    if use_screen and term is not None:
        print(term.clear, end="")
    bar = sep * 62
    print("\n" + bar)
    print(f"  Turn {turn_number}  |  {turn_label}")
    print(bar)
    board_text = board.display()
    print(board_text)
    you_label, opp_label = score_labels
    print(f"\n  Score — {you_label}: {p_score}  {opp_label}: {c_score}")
    lines = board_text.count("\n") + 1 + 2
    if note is not None:
        print(f"\n  {note}")
        lines += 2
    return lines


def run_game(
    player_hand: list[Card],
    cpu_hand: list[Card],
    rules: Collection[str],
    ai_mode: str,
    board_elements: list[Element | None] | None = None,
    ai_randomness: float = 0.0,
) -> str:
    """Run the full game loop until the board is full."""
    board = Board(elements=board_elements)
    term = _get_terminal()
    use_screen = term is not None and term.does_styling

    screen = term.fullscreen() if (use_screen and term is not None) else nullcontext()
    with screen:
        first = _decide_first(term if use_screen else None)

        turn = first
        turn_number = 1

        while any(board.is_empty(i) for i in range(BOARD_CELLS)):
            p_score, c_score = calculate_scores(board, player_hand, cpu_hand)
            turn_label = "YOUR TURN" if turn == "P" else "CPU TURN"
            _render_turn_screen(
                term, use_screen, board, turn_label, turn_number, p_score, c_score
            )

            if turn == "P":
                show_cpu = "Open" in rules
                display_hand(player_hand, "Your")
                display_hand(cpu_hand, "CPU", show=show_cpu)

                def _redraw(
                    turn_label: str = turn_label,
                    turn_number: int = turn_number,
                    p_score: int = p_score,
                    c_score: int = c_score,
                    show_cpu: bool = show_cpu,
                ) -> None:
                    _render_turn_screen(
                        term, use_screen, board, turn_label, turn_number, p_score, c_score
                    )
                    display_hand(player_hand, "Your")
                    display_hand(cpu_hand, "CPU", show=show_cpu)

                while True:
                    raw = input(f"\n  Choose card (1-{len(player_hand)}) [r=redraw]: ")
                    if raw.strip().lower() == "r":
                        _redraw()
                        continue
                    try:
                        ci = int(raw) - 1
                        if 0 <= ci < len(player_hand):
                            break
                        print(f"  ✗ Enter a number between 1 and {len(player_hand)}.")
                    except ValueError:
                        print("  ✗ Enter a number.")

                empty = [i for i in range(BOARD_CELLS) if board.is_empty(i)]
                while True:
                    raw = input(f"  Choose position (1-{BOARD_CELLS}) [r=redraw]: ")
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

            else:
                print("\n  CPU is thinking...")
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
            cursor_row = _render_turn_screen(
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
                    animate_captures(term, cursor_row, captures, card.owner)
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

        if use_screen and term is not None:
            print(term.clear, end="")
        print("\n" + "═" * 62)
        print("  GAME OVER")
        print("═" * 62)
        print(board.display())

        p_final, c_final = calculate_final_scores(board)
        print(f"\n  Final Score — You: {p_final}  CPU: {c_final}")

        if p_final > c_final:
            print("\n  🏆  YOU WIN!  Congratulations!")
            pause_message()
            return "P"
        elif c_final > p_final:
            print("\n  💀  CPU WINS!  Better luck next time!")
            pause_message()
            return "CPU"
        else:
            print("\n  🤝  IT'S A DRAW!")
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
    with screen:
        while any(board.is_empty(i) for i in range(BOARD_CELLS)):
            p_score, c_score = calculate_scores(board, player_hand, opponent_hand)
            turn_label = "YOUR TURN" if turn == "P" else "OPPONENT TURN"

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
                )

            is_local_turn = (turn == "P" and local_role == "P1") or (
                turn == "CPU" and local_role == "P2"
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
                    ci_index = player_hand.index(card)
                    player_hand.pop(ci_index)
                    card.owner = "P"
                    board.place(pos, card)
                    conn.send(make_move(ci_index, pos))
                move_note = f"You placed [{card.name}] at position {pos + 1}"
            else:
                if not headless and term:
                    print("\n  Opponent is thinking...")
                    display_hand(player_hand, "Your", show="Open" in rules)
                    display_hand(opponent_hand, "Opponent", show=True)

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
                cursor_row = _render_turn_screen(
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
                        animate_captures(term, cursor_row, captures, card.owner)
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

        if not headless and term:
            if use_screen:
                print(term.clear, end="")
            print("\n" + "=" * 62)
            print("  GAME OVER")
            print("=" * 62)
            print(board.display())
            print(f"\n  Final Score - You: {p_final}  Opponent: {c_final}")

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
            print(f"\n  {label}")
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
    display_hand(player_hand, "Your")
    display_hand(opponent_hand, "Opponent", show=show_opp)

    def _redraw() -> None:
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
        )
        display_hand(player_hand, "Your")
        display_hand(opponent_hand, "Opponent", show=show_opp)

    while True:
        raw = input(f"\n  Choose card (1-{len(player_hand)}) [r=redraw]: ")
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

    empty = [i for i in range(BOARD_CELLS) if board.is_empty(i)]
    while True:
        raw = input(f"  Choose position (1-{BOARD_CELLS}) [r=redraw]: ")
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
