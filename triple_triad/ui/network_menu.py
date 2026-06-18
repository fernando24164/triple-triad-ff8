"""Blessed-powered terminal UI for P2P multiplayer lobby screens."""

from __future__ import annotations

import logging
import random
import socket
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from blessed import Terminal


from ..data.cards import CARDS, Element
from ..deck.builder import build_random_deck
from ..models.card import Card
from ..network.connection import P2PConnection, perform_handshake
from ..network.protocol import (
    DEFAULT_PORT,
    HANDSHAKE_TIMEOUT_S,
    MessageType,
    make_deck_share,
    make_game_start,
    make_game_start_ack,
    make_sync_ack,
    make_sync_error,
    make_sync_setup,
    parse_packet,
)
from ..synth.sfx import play_cancel, play_confirm, play_error
from ..ui.cli import term

logger = logging.getLogger(__name__)


def _local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip  # type: ignore[no-any-return]
    except Exception:
        return "127.0.0.1"


def _center_x(term: Terminal, text: str) -> int:
    return max(0, (term.width - len(text)) // 2)


def _draw_frame(term: Terminal, title: str, subtitle: str = "") -> None:
    print(term.clear)
    print(
        term.move_yx(1, _center_x(term, "TRIPLE TRIAD"))
        + term.bold_cyan("TRIPLE TRIAD")
    )
    print(term.move_yx(2, _center_x(term, title)) + term.cyan(title))
    if subtitle:
        print(term.move_yx(3, _center_x(term, subtitle)) + term.dim + subtitle)


# ── Host Game Screen ─────────────────────────────────────────────────────────


def host_game_ui() -> tuple[P2PConnection, dict[str, Any]] | None:
    """Display host lobby screen, wait for a guest to connect.

    Returns (connection, handshake_payload) on success, None on cancel.
    """
    conn = P2PConnection(player_name="Host")

    port = DEFAULT_PORT
    hosting_started = False
    spinner = [" ", "/", "-", "\\"]
    spin_idx = 0

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            _draw_frame(term, "HOST GAME", f"Port: {port}")

            ip = _local_ip()
            info_lines = [
                f"Your IP: {ip}",
                f"Port:    {port}",
                "",
                "Waiting for opponent to connect...",
                "",
                f"  [{spinner[spin_idx]}] Listening...",
            ]

            y = term.height // 2 - len(info_lines) // 2
            for i, line in enumerate(info_lines):
                print(term.move_yx(y + i, _center_x(term, line)) + term.white(line))

            help_text = "Enter connect  •  Esc/q back"
            print(
                term.move_yx(term.height - 2, _center_x(term, help_text))
                + term.dim
                + help_text
            )

            if not conn.connected:
                if not hosting_started:
                    conn.host(port)
                    hosting_started = True

                k = term.inkey(timeout=0.2)
                if k and (k.name == "KEY_ESCAPE" or str(k).lower() == "q"):
                    play_cancel()
                    conn.close()
                    return None

                if not conn.connected and conn._server_sock is not None:
                    if conn.accept(timeout=0.0):
                        payload = perform_handshake(conn, timeout=HANDSHAKE_TIMEOUT_S)
                        if payload is None:
                            conn.connected = False
                            conn._cleanup_socket()
                            hosting_started = False
                            play_error()
                            continue
                        conn.remote_name = payload.get("player_name", "Guest")
                        _draw_frame(
                            term, "HOST GAME", "Connected! Exchanging handshakes..."
                        )
                        print(
                            term.move_yx(
                                term.height // 2 + 2,
                                _center_x(term, f"Opponent: {conn.remote_name}"),
                            )
                            + term.bold_green(f"Opponent: {conn.remote_name}")
                        )
                        time.sleep(0.5)
                        return conn, payload
                    else:
                        spin_idx = (spin_idx + 1) % len(spinner)
                        continue

    return None


# ── Join Game Screen ─────────────────────────────────────────────────────────


def join_game_ui() -> tuple[P2PConnection, dict[str, Any]] | None:
    """Display join lobby screen, prompt for host IP/port and connect.

    Returns (connection, handshake_payload) on success, None on cancel.
    """
    conn = P2PConnection(player_name="Guest")

    host_ip = ""
    port_str = str(DEFAULT_PORT)
    phase = "ip"  # ip -> port -> connecting -> handshake
    error_msg = ""
    timeout_start = 0.0

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            _draw_frame(term, "JOIN GAME", "Connect to a host")

            y = term.height // 2 - 4

            if phase == "ip":
                print(
                    term.move_yx(y, _center_x(term, "Host IP Address:"))
                    + term.cyan("Host IP Address:")
                )
                print(
                    term.move_yx(y + 1, _center_x(term, f"> {host_ip}_"))
                    + term.bold_white(f"> {host_ip}_")
                )
                if error_msg:
                    print(
                        term.move_yx(y + 3, _center_x(term, error_msg))
                        + term.red(error_msg)
                    )
                help_text = "Type IP  •  Enter confirm  •  Esc/q back"
                print(
                    term.move_yx(term.height - 2, _center_x(term, help_text))
                    + term.dim
                    + help_text
                )

                k = term.inkey(timeout=0.1)
                if not k:
                    continue
                if k.name == "KEY_ESCAPE" or str(k).lower() == "q":
                    play_cancel()
                    conn.close()
                    return None
                if k.name == "KEY_ENTER" or k == "\n":
                    play_confirm()
                    if not host_ip.strip():
                        error_msg = "Enter a valid IP address"
                        continue
                    phase = "port"
                    continue
                if k.name == "KEY_BACKSPACE" or str(k) == "\x7f":
                    host_ip = host_ip[:-1]
                    continue
                if not k.is_sequence and len(str(k)) == 1:
                    host_ip += str(k)

            elif phase == "port":
                print(
                    term.move_yx(y, _center_x(term, f"Host: {host_ip}"))
                    + term.cyan(f"Host: {host_ip}")
                )
                print(
                    term.move_yx(y + 1, _center_x(term, "Port:")) + term.cyan("Port:")
                )
                print(
                    term.move_yx(y + 2, _center_x(term, f"> {port_str}_"))
                    + term.bold_white(f"> {port_str}_")
                )
                help_text = "Type port  •  Enter connect  •  Esc/q back"
                print(
                    term.move_yx(term.height - 2, _center_x(term, help_text))
                    + term.dim
                    + help_text
                )

                k = term.inkey(timeout=0.1)
                if not k:
                    continue
                if k.name == "KEY_ESCAPE" or str(k).lower() == "q":
                    play_cancel()
                    conn.close()
                    return None
                if k.name == "KEY_ENTER" or k == "\n":
                    play_confirm()
                    try:
                        port = int(port_str)
                        phase = "connecting"
                        timeout_start = time.monotonic()
                    except ValueError:
                        error_msg = "Invalid port number"
                        continue
                if k.name == "KEY_BACKSPACE" or str(k) == "\x7f":
                    port_str = port_str[:-1]
                    continue
                if not k.is_sequence and len(str(k)) == 1 and str(k).isdigit():
                    port_str += str(k)

            elif phase == "connecting":
                elapsed = time.monotonic() - timeout_start
                if elapsed > 10.0:
                    error_msg = "Connection timed out"
                    conn.close()
                    phase = "ip"
                    continue

                _draw_frame(term, "JOIN GAME", f"Connecting to {host_ip}:{port_str}...")
                bar_w = 30
                fill = int(bar_w * min(elapsed / 10.0, 1.0))
                bar = "[" + "#" * fill + "." * (bar_w - fill) + "]"
                y = term.height // 2
                print(term.move_yx(y, _center_x(term, bar)) + term.yellow(bar))
                print(
                    term.move_yx(y + 2, _center_x(term, f"{elapsed:.1f}s / 10.0s"))
                    + term.dim
                    + f"{elapsed:.1f}s / 10.0s"
                )

                k = term.inkey(timeout=0.2)
                if k and (k.name == "KEY_ESCAPE" or str(k).lower() == "q"):
                    play_cancel()
                    conn.close()
                    return None

                if not conn.connected:
                    if conn.connect(host_ip, port, timeout=1.0):
                        payload = perform_handshake(conn, timeout=HANDSHAKE_TIMEOUT_S)
                        if payload is None:
                            conn.connected = False
                            error_msg = "Handshake failed"
                            conn.close()
                            phase = "ip"
                            play_error()
                            continue
                        conn.remote_name = payload.get("player_name", "Host")
                        _draw_frame(
                            term, "JOIN GAME", "Connected! Exchanging handshakes..."
                        )
                        print(
                            term.move_yx(
                                term.height // 2 + 2,
                                _center_x(term, f"Opponent: {conn.remote_name}"),
                            )
                            + term.bold_green(f"Opponent: {conn.remote_name}")
                        )
                        time.sleep(0.5)
                        return conn, payload
                    else:
                        continue

    return None


# ── Lobby Sync ───────────────────────────────────────────────────────────────


def lobby_sync_ui(
    conn: P2PConnection,
    is_host: bool,
    headless: bool = False,
) -> dict[str, Any] | None:
    """Run the lobby synchronization: exchange decks, sync rules, start game.

    On the host side, this runs the rule/board/deck selectors.
    Sends SYNC_SETUP to guest.
    Exchanges DECK_SHARE packets.
    Returns sync context dict on success, None on failure.

    In headless mode, uses default rules and random decks.
    """
    sync_ctx: dict[str, Any] = {}
    sync_timeout = 10.0 if headless else 120.0

    if is_host:
        if headless:
            rules: set[str] = {"Open"}
            board_elements: list[Element | None] = [None] * 9
            player_hand = build_random_deck()
            for c in player_hand:
                c.owner = "P"
            first_turn = random.choice(["P", "CPU"])
        else:
            from ..deck.picker import choose_deck
            from ..ui.cli import choose_board_ui, choose_rules_ui

            rules = choose_rules_ui()
            board_elements = choose_board_ui()
            player_hand = choose_deck()
            if not player_hand:
                conn.send(make_sync_error("Invalid local deck"))
                if not headless:
                    print("  Host: deck selection returned empty.")
                return None
            first_turn = random.choice(["P", "CPU"])

        board_elements_serialized: list[str | None] = [
            e.value if isinstance(e, Element) else None for e in board_elements
        ]
        sync_setup = make_sync_setup(
            rules=sorted(rules),
            board_elements=board_elements_serialized,
            first_turn=first_turn,
        )
        conn.send(sync_setup)
        logger.debug("Host: sent SYNC_SETUP, waiting for guest ack")

        # Wait for guest ack
        packet = conn.queue_get_filtered(
            {MessageType.SYNC_ACK, MessageType.SYNC_ERROR, MessageType.CONNECTION_LOST},
            timeout=sync_timeout,
        )
        if packet is None:
            logger.warning("Host: timeout waiting for guest SYNC_ACK")
            if not headless:
                print("  Sync timeout waiting for guest ack.")
            return None
        msg_type, _ = parse_packet(packet)
        logger.debug("Host: received %s while waiting for SYNC_ACK", msg_type)
        if msg_type != MessageType.SYNC_ACK:
            logger.warning("Host: expected SYNC_ACK, got %s", msg_type)
            if not headless:
                print(f"  Host: expected SYNC_ACK, got {msg_type}.")
            return None

        # Send deck
        card_names = [c.name for c in player_hand]
        conn.send(make_deck_share(card_names))

        # Receive guest deck
        logger.debug("Host: waiting for guest DECK_SHARE")
        packet = conn.queue_get_filtered(
            {
                MessageType.DECK_SHARE,
                MessageType.SYNC_ERROR,
                MessageType.CONNECTION_LOST,
            },
            timeout=sync_timeout,
        )
        if packet is None:
            logger.warning("Host: timeout waiting for guest DECK_SHARE")
            if not headless:
                print("  Host: timeout waiting for guest DECK_SHARE.")
            return None
        msg_type, payload = parse_packet(packet)
        logger.debug("Host: received %s while waiting for DECK_SHARE", msg_type)
        if msg_type != MessageType.DECK_SHARE:
            logger.warning("Host: expected DECK_SHARE, got %s", msg_type)
            if not headless:
                print(f"  Host: expected DECK_SHARE, got {msg_type}.")
            return None

        guest_names = payload.get("card_names", [])
        guest_hand = _validate_deck(guest_names)
        if guest_hand is None:
            conn.send(make_sync_error("Invalid guest deck"))
            if not headless:
                print("  Host: guest deck validation failed.")
            return None
        for c in guest_hand:
            c.owner = "CPU"

        sync_ctx = {
            "rules": rules,
            "board_elements": board_elements,
            "player_hand": player_hand,
            "opponent_hand": guest_hand,
            "first_turn": first_turn,
        }
    else:
        # Guest: receive sync_setup
        logger.debug("Guest: waiting for SYNC_SETUP (timeout=%.1fs)", sync_timeout)
        packet = conn.queue_get_filtered(
            {
                MessageType.SYNC_SETUP,
                MessageType.SYNC_ERROR,
                MessageType.CONNECTION_LOST,
            },
            timeout=sync_timeout,
        )
        if packet is None:
            logger.warning("Guest: timeout waiting for SYNC_SETUP")
            if not headless:
                print("  Guest: timeout waiting for SYNC_SETUP.")
            return None
        msg_type, payload = parse_packet(packet)
        logger.debug("Guest: received %s while waiting for SYNC_SETUP", msg_type)
        if msg_type != MessageType.SYNC_SETUP:
            logger.warning("Guest: expected SYNC_SETUP, got %s", msg_type)
            if not headless:
                print(f"  Guest: expected SYNC_SETUP, got {msg_type}.")
            return None

        rules_list = payload.get("rules", [])
        rules = set(rules_list)
        elements_raw = payload.get("board_elements", [None] * 9)
        board_elements = [
            Element(e)
            if isinstance(e, str) and e in [el.value for el in Element]
            else None
            for e in elements_raw
        ]
        first_turn = payload.get("first_turn", "P")

        if headless:
            player_hand = build_random_deck()
        else:
            from ..deck.picker import choose_deck

            player_hand = choose_deck()
            if not player_hand:
                conn.send(make_sync_error("Invalid local deck"))
                if not headless:
                    print("  Guest: deck selection returned empty.")
                return None
        for c in player_hand:
            c.owner = "P"

        # Send ack
        conn.send(make_sync_ack())

        # Send deck
        card_names = [c.name for c in player_hand]
        conn.send(make_deck_share(card_names))

        # Receive host deck
        logger.debug("Guest: waiting for host DECK_SHARE")
        packet = conn.queue_get_filtered(
            {
                MessageType.DECK_SHARE,
                MessageType.SYNC_ERROR,
                MessageType.CONNECTION_LOST,
            },
            timeout=sync_timeout,
        )
        if packet is None:
            logger.warning("Guest: timeout waiting for host DECK_SHARE")
            if not headless:
                print("  Guest: timeout waiting for host DECK_SHARE.")
            return None
        msg_type, payload = parse_packet(packet)
        logger.debug("Guest: received %s while waiting for DECK_SHARE", msg_type)
        if msg_type != MessageType.DECK_SHARE:
            logger.warning("Guest: expected DECK_SHARE, got %s", msg_type)
            if not headless:
                print(f"  Guest: expected DECK_SHARE, got {msg_type}.")
            return None

        host_names = payload.get("card_names", [])
        host_hand = _validate_deck(host_names)
        if host_hand is None:
            conn.send(make_sync_error("Invalid host deck"))
            if not headless:
                print("  Guest: host deck validation failed.")
            return None
        for c in host_hand:
            c.owner = "CPU"

        sync_ctx = {
            "rules": rules,
            "board_elements": board_elements,
            "player_hand": player_hand,
            "opponent_hand": host_hand,
            "first_turn": first_turn,
        }

    # ── GAME_START two-way handshake ──────────────────────────────────────
    # Both sides send GAME_START and wait for the peer's GAME_START,
    # then exchange GAME_START_ACK to confirm readiness.
    logger.debug("Lobby: sending GAME_START")
    conn.send(make_game_start())

    packet = conn.queue_get_filtered(
        {
            MessageType.GAME_START,
            MessageType.GAME_START_ACK,
            MessageType.CONNECTION_LOST,
        },
        timeout=sync_timeout,
    )
    if packet is None:
        logger.warning("Lobby: timeout waiting for GAME_START")
        if not headless:
            print("  Sync: timeout waiting for GAME_START.")
        return None
    msg_type, _ = parse_packet(packet)
    logger.debug("Lobby: received %s during GAME_START handshake", msg_type)
    if msg_type == MessageType.CONNECTION_LOST:
        logger.warning("Lobby: connection lost during GAME_START handshake")
        if not headless:
            print("  Sync: connection lost during GAME_START handshake.")
        return None

    if msg_type == MessageType.GAME_START:
        conn.send(make_game_start_ack())
        packet = conn.queue_get_filtered(
            {MessageType.GAME_START_ACK, MessageType.CONNECTION_LOST},
            timeout=sync_timeout,
        )
        if packet is None:
            logger.warning("Lobby: timeout waiting for GAME_START_ACK")
            if not headless:
                print("  Sync: timeout waiting for GAME_START_ACK.")
            return None
        msg_type, _ = parse_packet(packet)
        logger.debug("Lobby: received %s, expecting GAME_START_ACK", msg_type)
        if msg_type != MessageType.GAME_START_ACK:
            if not headless:
                print(f"  Sync: expected GAME_START_ACK, got {msg_type}.")
            return None

    # msg_type == GAME_START_ACK — peer already processed our GAME_START
    return sync_ctx


def _validate_deck(card_names: list[str]) -> list[Card] | None:
    """Validate card names against the CARDS database."""
    hand = []
    for name in card_names:
        if name not in CARDS:
            return None
        hand.append(Card(name))
    if len(hand) != 5:
        return None
    return hand
