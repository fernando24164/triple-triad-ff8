from __future__ import annotations

import random
import time
from collections.abc import Collection
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


def _decide_first() -> str:
    """Animate a bouncing selector between YOU and CPU, then reveal who goes first."""
    term = _get_terminal()
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

    print(term.normal + term.clear, end="")
    return first


def _display_board_text(
    board: Board, turn: str, turn_number: int, p_score: int, c_score: int
) -> None:
    print("\n" + "=" * 62)
    print(f"  Turn {turn_number}  |  {'YOUR TURN' if turn == 'P' else 'OPPONENT TURN'}")
    print("=" * 62)
    print(board.display())
    print(f"\n  Score - You: {p_score}  Opponent: {c_score}")


def run_game(
    player_hand: list[Card],
    cpu_hand: list[Card],
    rules: Collection[str],
    ai_mode: str,
    board_elements: list[Element | None] | None = None,
) -> str:
    """Run the full game loop until the board is full."""
    board = Board(elements=board_elements)
    first = _decide_first()

    turn = first
    turn_number = 1

    while any(board.is_empty(i) for i in range(BOARD_CELLS)):
        print("\n" + "═" * 62)
        print(f"  Turn {turn_number}  |  {'YOUR TURN' if turn == 'P' else 'CPU TURN'}")
        print("═" * 62)
        print(board.display())

        p_score, c_score = calculate_scores(board, player_hand, cpu_hand)
        print(f"\n  Score — You: {p_score}  CPU: {c_score}")

        if turn == "P":
            show_cpu = "Open" in rules
            display_hand(player_hand, "Your")
            display_hand(cpu_hand, "CPU", show=show_cpu)

            while True:
                try:
                    ci = int(input(f"\n  Choose card (1-{len(player_hand)}): ")) - 1
                    if 0 <= ci < len(player_hand):
                        break
                    print(f"  ✗ Enter a number between 1 and {len(player_hand)}.")
                except ValueError:
                    print("  ✗ Enter a number.")

            empty = [i for i in range(BOARD_CELLS) if board.is_empty(i)]
            while True:
                try:
                    pos = int(input(f"  Choose position (1-{BOARD_CELLS}): ")) - 1
                    if pos in empty:
                        break
                    print("  ✗ Position taken or invalid.")
                except ValueError:
                    print("  ✗ Enter a number.")

            card = player_hand.pop(ci)
            card.owner = "P"
            board.place(pos, card)
            print(f"\n  You placed [{card.name}] at position {pos + 1}")

        else:
            print("\n  CPU is thinking...")
            ci, cpu_pos = cpu_choose(board, cpu_hand, rules, mode=ai_mode)
            assert cpu_pos is not None, "CPU had no valid move on a non-full board"
            card = cpu_hand.pop(ci)
            card.owner = "CPU"
            board.place(cpu_pos, card)
            print(f"  CPU placed [{card.name}] at position {cpu_pos + 1}")
            pos = cpu_pos

        captures, events = resolve_captures(board, pos, card, rules)
        for evt in events:
            print(f"  *** {evt.upper()}! ***")
        for _, ncard in captures:
            old_owner = ncard.owner
            ncard.owner = card.owner
            attacker_label = "You" if card.owner == "P" else "CPU"
            defender_label = "CPU" if old_owner == "CPU" else "You"
            print(
                f"  ⚔  [{card.name}] captured [{ncard.name}]! "
                f"({defender_label} → {attacker_label})"
            )

        turn = "CPU" if turn == "P" else "P"
        turn_number += 1

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

    while any(board.is_empty(i) for i in range(BOARD_CELLS)):
        p_score, c_score = calculate_scores(board, player_hand, opponent_hand)

        if not headless and term:
            _display_board_text(board, turn, turn_number, p_score, c_score)

        is_local_turn = (turn == "P" and local_role == "P1") or (
            turn == "CPU" and local_role == "P2"
        )

        pos = -1
        card = None

        if is_local_turn:
            if headless:
                ci, cpu_pos = cpu_choose(board, player_hand, rules, mode="greedy")
                assert cpu_pos is not None
                pos = cpu_pos
                card = player_hand.pop(ci)
                card.owner = "P"
                board.place(pos, card)
                if not headless and term:
                    print(f"\n  You placed [{card.name}] at position {pos + 1}")
                conn.send(make_move(ci, pos))
            else:
                card, pos = _get_local_move_interactive(
                    board, player_hand, opponent_hand, rules, term, local_role
                )
                ci_index = player_hand.index(card)
                player_hand.pop(ci_index)
                card.owner = "P"
                board.place(pos, card)
                if term:
                    print(f"\n  You placed [{card.name}] at position {pos + 1}")
                conn.send(make_move(ci_index, pos))
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
            if not headless and term:
                print(f"  Opponent placed [{card.name}] at position {pos + 1}")

        assert card is not None and pos >= 0
        captures, events = resolve_captures(board, pos, card, rules)
        if not headless and term:
            for evt in events:
                print(f"  *** {evt.upper()}! ***")
            for _, ncard in captures:
                old_owner = ncard.owner
                ncard.owner = card.owner
                attacker_label = "You" if card.owner == "P" else "Opponent"
                defender_label = "Opponent" if old_owner == "CPU" else "You"
                print(
                    f"  [{card.name}] captured [{ncard.name}]! "
                    f"({defender_label} -> {attacker_label})"
                )

        turn = "CPU" if turn == "P" else "P"
        turn_number += 1

    p_final, c_final = calculate_final_scores(board)

    if not headless and term:
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
) -> tuple[Card, int]:
    """Get a move from the local player via keyboard input."""
    show_opp = "Open" in rules
    display_hand(player_hand, "Your")
    display_hand(opponent_hand, "Opponent", show=show_opp)

    while True:
        try:
            ci = int(input(f"\n  Choose card (1-{len(player_hand)}): ")) - 1
            if 0 <= ci < len(player_hand):
                break
            print(f"  Enter a number between 1 and {len(player_hand)}.")
        except ValueError:
            print("  Enter a number.")

    empty = [i for i in range(BOARD_CELLS) if board.is_empty(i)]
    while True:
        try:
            pos = int(input(f"  Choose position (1-{BOARD_CELLS}): ")) - 1
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
