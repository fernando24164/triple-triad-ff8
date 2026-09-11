from __future__ import annotations

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
from ..models.player import MatchResult, Player, Role
from ..network.connection import P2PConnection
from ..network.protocol import (
    MOVE_TIMEOUT_S,
    MessageType,
    make_disconnect,
    make_forfeit,
    make_move,
    parse_packet,
)
from ..synth.sfx import play_cancel, play_capture_lose, play_capture_win
from ..synth.wave_generators import generate_boogie_buffer, generate_music_buffer
from ..ui.capture_fx import animate_captures
from ..ui.cli import pause_message
from ..ui.match_controller import TurnContext, get_local_move
from ..ui.match_view import (
    decide_first,
    hand_block_lines,
    render_game_over_screen,
    render_turn_screen,
    reveal_first,
    show_match_outcome,
)
from ..ui.position_selector import QuitGameError
from ..ui.terminal import term
from .rules import apply_captures, resolve_captures
from .scoring import calculate_final_scores, calculate_scores


def _get_terminal() -> Terminal | None:
    return term


@contextmanager
def _boogie_during_match(music_player: ChiptunePlayer | None) -> Iterator[None]:
    """Swap the main menu music for the gameplay 'boogie' theme while cards
    are being played, then swap back to the menu theme — however the block
    exits (normal return, early return, or exception). A no-op when
    there's no shared player (headless mode, tests).
    """
    if music_player is None:
        yield
        return
    music_player.switch_track(generate_boogie_buffer)
    try:
        yield
    finally:
        music_player.switch_track(generate_music_buffer)


def run_game(
    player_hand: list[Card],
    cpu_hand: list[Card],
    rules: Collection[str],
    ai_mode: str,
    board_elements: list[Element | None] | None = None,
    ai_randomness: float = 0.0,
    music_player: ChiptunePlayer | None = None,
) -> MatchResult:
    """Run the full game loop until the board is full."""
    board = Board(elements=board_elements)
    term = _get_terminal()
    use_screen = term is not None and term.does_styling

    screen = term.fullscreen() if (use_screen and term is not None) else nullcontext()
    with screen, _boogie_during_match(music_player):
        first = decide_first(term if use_screen else None)

        turn = first
        turn_number = 1

        while any(board.is_empty(i) for i in range(BOARD_CELLS)):
            p_score, c_score = calculate_scores(board, player_hand, cpu_hand)
            turn_label = "YOUR TURN" if turn == Player.PLAYER else "CPU TURN"
            choose_extra = (
                hand_block_lines(len(player_hand)) + hand_block_lines(len(cpu_hand))
                if turn == Player.PLAYER
                else 2
            )
            render_turn_screen(
                term,
                use_screen,
                board,
                turn_label,
                turn_number,
                p_score,
                c_score,
                extra_lines=choose_extra,
            )

            if turn == Player.PLAYER:
                try:
                    card, pos = get_local_move(
                        TurnContext(
                            board=board,
                            player_hand=player_hand,
                            other_hand=cpu_hand,
                            other_label="CPU",
                            rules=rules,
                            term=term,
                            use_screen=use_screen,
                            turn_label=turn_label,
                            turn_number=turn_number,
                            p_score=p_score,
                            c_score=c_score,
                        )
                    )
                    card = player_hand.pop(player_hand.index(card))
                    card.owner = Player.PLAYER
                    board.place(pos, card)
                    move_note = f"You placed [{card.name}] at position {pos + 1}"
                except QuitGameError:
                    play_cancel()
                    return MatchResult.QUIT

            else:
                print("\n  CPU is thinking...")
                if use_screen:
                    time.sleep(0.5)
                ci, cpu_pos = cpu_choose(
                    board, cpu_hand, rules, mode=ai_mode, randomness=ai_randomness
                )
                assert cpu_pos is not None, "CPU had no valid move on a non-full board"
                card = cpu_hand.pop(ci)
                card.owner = Player.CPU
                board.place(cpu_pos, card)
                pos = cpu_pos
                move_note = f"CPU placed [{card.name}] at position {pos + 1}"

            captures, events = resolve_captures(board, pos, card, rules)

            cursor_row, col_offset = render_turn_screen(
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
                    render_turn_screen(
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
                    apply_captures(captures, card.owner)
                play_capture_win() if card.owner == Player.PLAYER else play_capture_lose()
            if not use_screen:
                for evt in events:
                    print(f"  *** {evt.upper()}! ***")
            attacker_label = "You" if card.owner == Player.PLAYER else "CPU"
            for cap_pos, ncard in captures:
                old_owner = old_owners[cap_pos]
                defender_label = "CPU" if old_owner == Player.CPU else "You"
                print(
                    f"  ⚔  [{card.name}] captured [{ncard.name}]! "
                    f"({defender_label} → {attacker_label})"
                )
            apply_captures(captures, card.owner)

            if use_screen:
                time.sleep(0.9)

            turn = Player.CPU if turn == Player.PLAYER else Player.PLAYER
            turn_number += 1

        p_final, c_final = calculate_final_scores(board)

        if p_final > c_final:
            outcome = MatchResult.P1_WIN
            result_text = "🏆  YOU WIN!  Congratulations!"
        elif c_final > p_final:
            outcome = MatchResult.P2_WIN
            result_text = "💀  CPU WINS!  Better luck next time!"
        else:
            outcome = MatchResult.DRAW
            result_text = "🤝  IT'S A DRAW!"

        render_game_over_screen(
            term, use_screen, board, p_final, c_final, result_text=result_text
        )
        show_match_outcome(
            term, use_screen, board, p_final, c_final, result_text, outcome
        )
        return outcome


def run_p2p_game(
    conn: P2PConnection,
    player_hand: list[Card],
    opponent_hand: list[Card],
    rules: Collection[str],
    board_elements: list[Element | None] | None,
    local_role: Role,
    first_turn: Player,
    headless: bool = False,
    music_player: ChiptunePlayer | None = None,
) -> MatchResult:
    """Run a P2P multiplayer game loop.

    Args:
        conn: Active P2P connection to the opponent.
        player_hand: Local player's hand (cards with owner='P').
        opponent_hand: Remote opponent's hand (cards with owner='CPU').
        rules: Active rules set.
        board_elements: Board element configuration.
        local_role: This client's seat (Role.P1 or Role.P2).
        first_turn: Who goes first (Player.PLAYER or Player.CPU).
        headless: If True, use AI for all local moves.
        music_player: Shared menu music player to duck while the match
            plays and restore afterward, or None to skip music switching.

    Returns:
        MatchResult.P1_WIN, P2_WIN, DRAW, or QUIT.
    """
    board = Board(elements=board_elements)
    turn = Player(first_turn)
    turn_number = 1
    term = _get_terminal() if not headless else None
    use_screen = not headless and term is not None and term.does_styling
    score_labels = ("You", "Opponent")

    screen = term.fullscreen() if (use_screen and term is not None) else nullcontext()
    with screen, _boogie_during_match(music_player if not headless else None):
        if not headless and use_screen and term is not None:
            local_first = (first_turn == Player.PLAYER) != (local_role == Role.P2)
            reveal_first(
                term,
                Player.PLAYER if local_first else Player.CPU,
                labels=("  YOU  ", "OPPONENT"),
                result_texts=("You go first!", "Opponent goes first!"),
            )

        while any(board.is_empty(i) for i in range(BOARD_CELLS)):
            p_score, c_score = calculate_scores(board, player_hand, opponent_hand)
            is_local_turn = (turn == Player.PLAYER and local_role == Role.P1) or (
                turn == Player.CPU and local_role == Role.P2
            )
            turn_label = "YOUR TURN" if is_local_turn else "OPPONENT TURN"
            choose_extra = (
                hand_block_lines(len(player_hand))
                + hand_block_lines(len(opponent_hand))
                if is_local_turn
                else 2
            )

            if not headless and term:
                render_turn_screen(
                    term,
                    use_screen,
                    board,
                    turn_label,
                    turn_number,
                    p_score,
                    c_score,
                    score_labels=score_labels,
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
                    card.owner = Player.PLAYER
                    board.place(pos, card)
                    conn.send(make_move(ci, pos))
                else:
                    try:
                        card, pos = get_local_move(
                            TurnContext(
                                board=board,
                                player_hand=player_hand,
                                other_hand=opponent_hand,
                                other_label="Opponent",
                                rules=rules,
                                term=term,
                                use_screen=use_screen,
                                turn_label=turn_label,
                                turn_number=turn_number,
                                p_score=p_score,
                                c_score=c_score,
                                score_labels=score_labels,
                            )
                        )
                    except QuitGameError:
                        conn.send(make_forfeit("Player quit"))
                        play_cancel()
                        return MatchResult.QUIT
                    ci_index = player_hand.index(card)
                    player_hand.pop(ci_index)
                    card.owner = Player.PLAYER
                    board.place(pos, card)
                    conn.send(make_move(ci_index, pos))
                move_note = f"You placed [{card.name}] at position {pos + 1}"
            else:
                if not headless and term:
                    print("\n  Opponent is thinking...", end="", flush=True)

                packet = _wait_for_move(conn, term, headless)
                if packet is None:
                    if not headless and term:
                        print("\n  Opponent took too long!")
                        pause_message()
                    return _win_by_opponent_error(local_role)

                msg_type, payload = parse_packet(packet)
                if msg_type == MessageType.FORFEIT:
                    if not headless and term:
                        reason = payload.get("reason", "")
                        print(f"\n  Opponent forfeited! {reason}")
                        pause_message()
                    return _win_by_opponent_error(local_role)

                if msg_type in (MessageType.DISCONNECT, MessageType.CONNECTION_LOST):
                    if not headless and term:
                        print("\n  Opponent disconnected!")
                        pause_message()
                    return _win_by_opponent_error(local_role)

                opp_ci = payload["card_idx"]
                opp_pos = payload["position"]

                if opp_ci < 0 or opp_ci >= len(opponent_hand):
                    conn.send(make_forfeit("Invalid card index"))
                    return _win_by_opponent_error(local_role)

                if opp_pos < 0 or opp_pos >= BOARD_CELLS or not board.is_empty(opp_pos):
                    conn.send(make_forfeit("Invalid position"))
                    return _win_by_opponent_error(local_role)

                opp_card = opponent_hand.pop(opp_ci)
                opp_card.owner = Player.CPU
                board.place(opp_pos, opp_card)
                card = opp_card
                pos = opp_pos
                move_note = f"Opponent placed [{card.name}] at position {pos + 1}"

            assert card is not None and pos >= 0
            captures, events = resolve_captures(board, pos, card, rules)
            if not headless and term:
                cursor_row, col_offset = render_turn_screen(
                    term,
                    use_screen,
                    board,
                    turn_label,
                    turn_number,
                    p_score,
                    c_score,
                    score_labels=score_labels,
                    note=move_note,
                )
                if captures:
                    old_owners = {cpos: ccard.owner for cpos, ccard in captures}
                    if use_screen:
                        animate_captures(
                            term, cursor_row, captures, card.owner, col_offset, events
                        )
                        render_turn_screen(
                            term,
                            use_screen,
                            board,
                            turn_label,
                            turn_number,
                            p_score,
                            c_score,
                            score_labels=score_labels,
                            note=move_note,
                        )
                    else:
                        apply_captures(captures, card.owner)
                    play_capture_win() if card.owner == Player.PLAYER else play_capture_lose()
                if not use_screen:
                    for evt in events:
                        print(f"  *** {evt.upper()}! ***")
                attacker_label = "You" if card.owner == Player.PLAYER else "Opponent"
                for cap_pos, ncard in captures:
                    old_owner = old_owners[cap_pos]
                    defender_label = "Opponent" if old_owner == Player.CPU else "You"
                    print(
                        f"  ⚔  [{card.name}] captured [{ncard.name}]! "
                        f"({defender_label} → {attacker_label})"
                    )
                apply_captures(captures, card.owner)
                if use_screen:
                    time.sleep(0.9)
            else:
                apply_captures(captures, card.owner)

            turn = Player.CPU if turn == Player.PLAYER else Player.PLAYER
            turn_number += 1

        p_final, c_final = calculate_final_scores(board)

        if p_final > c_final:
            result = MatchResult.P1_WIN if local_role == Role.P1 else MatchResult.P2_WIN
            local_outcome = MatchResult.P1_WIN
            result_text = "🏆  YOU WIN!  Congratulations!"
        elif c_final > p_final:
            result = MatchResult.P2_WIN if local_role == Role.P1 else MatchResult.P1_WIN
            local_outcome = MatchResult.P2_WIN
            result_text = "💀  OPPONENT WINS!  Better luck next time!"
        else:
            result = MatchResult.DRAW
            local_outcome = MatchResult.DRAW
            result_text = "🤝  IT'S A DRAW!"

        if not headless and term:
            render_game_over_screen(
                term,
                use_screen,
                board,
                p_final,
                c_final,
                score_labels=score_labels,
                result_text=result_text,
            )
            show_match_outcome(
                term,
                use_screen,
                board,
                p_final,
                c_final,
                result_text,
                local_outcome,
                score_labels=score_labels,
            )
        return result


def _win_by_opponent_error(local_role: Role) -> MatchResult:
    """The opponent erred/disconnected — the other seat wins."""
    return MatchResult.P1_WIN if local_role == Role.P2 else MatchResult.P2_WIN


def _wait_for_move(
    conn: P2PConnection,
    term: Terminal | None,
    headless: bool,
) -> dict[str, Any] | None:
    """Block waiting for a MOVE packet from the network, with heartbeat handling.

    Uses queue_get_filtered so non-matching packets (e.g. heartbeats) are
    buffered in ``_pending`` instead of silently discarded. The spinner
    overwrites the caller's "Opponent is thinking..." line in place, so the
    waiting message costs no extra rows and the centered board stays put.
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
            line = f"  Waiting for opponent... [{spinner[spin_idx]}] ({elapsed:.0f}s)"
            print("\r" + line.ljust(44), end="", flush=True)
            spin_idx = (spin_idx + 1) % len(spinner)

    conn.send(make_disconnect("Timeout"))
    return None


def run_headless_p2p_game(
    conn: P2PConnection,
    player_hand: list[Card],
    opponent_hand: list[Card],
    rules: Collection[str],
    board_elements: list[Element | None] | None,
    local_role: Role,
    first_turn: Player,
) -> MatchResult:
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
