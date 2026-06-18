import argparse
import logging
import os
import sys
import time
from typing import Any

from .deck.builder import (
    DIFFICULTY_CONFIG,
    build_cpu_deck,
    build_random_deck,
    build_starter_deck,
    get_cpu_ai_mode,
)
from .deck.deck_selector import choose_preset_deck
from .deck.picker import choose_deck
from .engine.game_loop import run_game
from .engine.tournament import run_tournament
from .models.card import Card
from .network.connection import P2PConnection, perform_handshake
from .network.protocol import (
    DEFAULT_PORT,
    HANDSHAKE_TIMEOUT_S,
)
from .synth.player import ChiptunePlayer
from .tutorial.tutorial_engine import run_tutorial
from .ui.cli import (
    choose_board_ui,
    choose_deck_mode_ui,
    choose_difficulty_ui,
    choose_rules_ui,
    choose_saved_deck_ui,
    deck_manager_ui,
    main_menu,
    new_game_menu,
    options_menu,
    pause_message,
    prompt_save_deck_ui,
    quit_menu,
)
from .ui.display import print_banner, print_help

logger = logging.getLogger(__name__)


def _setup_headless_env() -> None:
    """Force dummy drivers for headless execution."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"


def play_single_game() -> None:
    difficulty = choose_difficulty_ui()
    ai_mode = get_cpu_ai_mode(difficulty)
    rules = choose_rules_ui()
    board_elements = choose_board_ui()
    deck_mode = choose_deck_mode_ui()
    if deck_mode is None:
        return

    player_hand: list[Card]
    if deck_mode == "1":
        picked = choose_deck()
        if not picked:
            return
        player_hand = picked
        prompt_save_deck_ui(player_hand)
    elif deck_mode == "2":
        player_hand = build_starter_deck()
    elif deck_mode == "3":
        player_hand = build_random_deck()
    elif deck_mode == "5":
        loaded = choose_saved_deck_ui()
        if loaded is None:
            return
        player_hand = loaded
    else:
        player_hand = choose_preset_deck()

    cpu_hand = build_cpu_deck(difficulty)

    for c in player_hand:
        c.owner = "P"
    for c in cpu_hand:
        c.owner = "CPU"

    print("\n  -- Your Deck --")
    for c in player_hand:
        el = f"[{c.element}]" if c.element else ""
        print(
            f"    {c.name}{el}  ^{c.top} >{c.right} v{c.bottom} <{c.left}  Lv{c.level}"
        )

    cfg = DIFFICULTY_CONFIG[difficulty]
    print(
        f"\n  -- CPU Deck  (Lv {cfg['cpu_min_level']}-{cfg['cpu_max_level']}, "
        f"AI: {ai_mode}) --"
    )
    for c in cpu_hand:
        el = f"[{c.element}]" if c.element else ""
        print(
            f"    {c.name}{el}  ^{c.top} >{c.right} v{c.bottom} <{c.left}  Lv{c.level}"
        )

    run_game(player_hand, cpu_hand, rules, ai_mode, board_elements)
    pause_message()


def play_tournament() -> None:
    difficulty = choose_difficulty_ui()
    ai_mode = get_cpu_ai_mode(difficulty)
    board_elements = choose_board_ui()
    run_tournament(difficulty, ai_mode, board_elements)
    pause_message()


def play_multiplayer_game() -> None:
    """Interactive multiplayer flow with UI menus."""
    from .ui.network_menu import host_game_ui, join_game_ui, lobby_sync_ui

    type_items = ["Host Game", "Join Game", "Back"]
    from .ui.cli import selector

    sel = selector("Multiplayer", type_items)
    if sel is None or sel == 2:
        return

    is_host = sel == 0

    result = host_game_ui() if is_host else join_game_ui()

    if result is None:
        return

    conn, handshake_payload = result

    # Run lobby sync
    sync_ctx = lobby_sync_ui(conn, is_host=is_host, headless=False)
    if sync_ctx is None:
        print("\n  Lobby sync failed.")
        conn.close()
        pause_message()
        return

    local_role = "P1" if is_host else "P2"
    try:
        game_result = run_p2p_game_from_ctx(conn, sync_ctx, local_role, headless=False)
    except Exception as exc:
        logger.error("P2P game error: %s", exc)
        game_result = "DRAW"
    finally:
        conn.close()

    print(f"\n  Game result: {game_result}")
    pause_message()


def run_p2p_game_from_ctx(
    conn: P2PConnection,
    sync_ctx: dict[str, Any],
    local_role: str,
    headless: bool = False,
) -> str:
    """Run a P2P game from a synchronization context dict."""
    from .data.cards import Element
    from .engine.game_loop import run_p2p_game

    rules = sync_ctx["rules"]
    raw_elements = sync_ctx["board_elements"]
    board_elements = [Element(e) if isinstance(e, str) else None for e in raw_elements]
    player_hand = sync_ctx["player_hand"]
    opponent_hand = sync_ctx["opponent_hand"]
    first_turn = sync_ctx["first_turn"]

    return run_p2p_game(
        conn=conn,
        player_hand=player_hand,
        opponent_hand=opponent_hand,
        rules=rules,
        board_elements=board_elements,
        local_role=local_role,
        first_turn=first_turn,
        headless=headless,
    )


def run_headless_host_test(port: int = DEFAULT_PORT) -> int:
    """Headless host: boot into lobby, wait for guest, play game, return exit code."""
    _setup_headless_env()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    logger.info("Listening on port %d...", port)
    conn = P2PConnection(player_name="TestHost")
    conn.host(port)

    # Wait for guest
    logger.info("Waiting for guest to connect...")
    while not conn.connected:
        if conn.accept(timeout=0.5):
            break
        time.sleep(0.1)

    logger.info("Connected! Sending handshake...")
    payload = perform_handshake(conn, timeout=HANDSHAKE_TIMEOUT_S)
    if payload is None:
        logger.info("Handshake failed")
        conn.close()
        return 1
    conn.remote_name = payload.get("player_name", "Guest")
    logger.info("Handshake from %s", conn.remote_name)

    # Setup sync
    from .ui.network_menu import lobby_sync_ui

    sync_ctx = lobby_sync_ui(conn, is_host=True, headless=True)
    if sync_ctx is None:
        logger.info("Lobby sync failed")
        conn.close()
        return 1

    logger.info("Sync complete. Starting game...")
    try:
        result = run_p2p_game_from_ctx(conn, sync_ctx, "P1", headless=True)
    except Exception as exc:
        logger.info("Game error: %s", exc)
        result = "DRAW"
    finally:
        conn.close()

    p1_cards = sum(1 for c in sync_ctx["player_hand"])
    p2_cards = sum(1 for c in sync_ctx["opponent_hand"])
    logger.info("Game finished. Result: %s", result)
    logger.info("Host cards remaining: %d, Guest cards: %d", p1_cards, p2_cards)
    return 0


def run_headless_join_test(host_ip: str, port: int = DEFAULT_PORT) -> int:
    """Headless guest: connect to host, play game, return exit code."""
    _setup_headless_env()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    logger.info("Connecting to %s:%d...", host_ip, port)
    conn = P2PConnection(player_name="TestGuest")

    if not conn.connect(host_ip, port, timeout=10.0):
        logger.info("Connection failed")
        return 1

    logger.info("Connected! Sending handshake...")
    payload = perform_handshake(conn, timeout=HANDSHAKE_TIMEOUT_S)
    if payload is None:
        logger.info("Handshake failed")
        conn.close()
        return 1
    conn.remote_name = payload.get("player_name", "Host")
    logger.info("Handshake from %s", conn.remote_name)

    # Setup sync
    from .ui.network_menu import lobby_sync_ui

    sync_ctx = lobby_sync_ui(conn, is_host=False, headless=True)
    if sync_ctx is None:
        logger.info("Lobby sync failed")
        conn.close()
        return 1

    logger.info("Sync complete. Starting game...")
    try:
        result = run_p2p_game_from_ctx(conn, sync_ctx, "P2", headless=True)
    except Exception as exc:
        logger.info("Game error: %s", exc)
        result = "DRAW"
    finally:
        conn.close()

    logger.info("Game finished. Result: %s", result)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Triple Triad - Final Fantasy VIII card game", add_help=False
    )
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show game tutorial and help"
    )
    parser.add_argument(
        "-m", "--no-music", action="store_true", help="Disable background music"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no terminal UI, no audio)",
    )
    parser.add_argument(
        "--host-test",
        action="store_true",
        help="Headless host mode: boot into lobby, wait for guest, play game",
    )
    parser.add_argument(
        "--join-test",
        type=str,
        default=None,
        metavar="HOST_IP",
        help="Headless join mode: connect to host and play game",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port for host/join test (default: {DEFAULT_PORT})",
    )
    args = parser.parse_args()

    if args.help:
        print_help()
        sys.exit(0)

    # Headless modes
    if args.host_test:
        exit_code = run_headless_host_test(args.port)
        sys.exit(exit_code)

    if args.join_test is not None:
        exit_code = run_headless_join_test(args.join_test, args.port)
        sys.exit(exit_code)

    if args.headless:
        _setup_headless_env()

    print_banner()

    music_player = ChiptunePlayer()
    music_on = not args.no_music and not args.headless
    if music_on:
        music_player.start()

    try:
        while True:
            choice = main_menu()
            if choice == "quit":
                if quit_menu() == "exit":
                    break
            elif choice == "tutorial":
                run_tutorial()
            elif choice == "deck_manager":
                deck_manager_ui()
            elif choice == "options":
                result = options_menu(music_on)
                if result == "toggle_music":
                    if music_on:
                        music_player.stop()
                        music_on = False
                    else:
                        music_player.start()
                        music_on = True
            elif choice == "new_game":
                game_type = new_game_menu()
                if game_type == "single":
                    play_single_game()
                elif game_type == "tournament":
                    play_tournament()
                elif game_type == "multiplayer":
                    play_multiplayer_game()
    finally:
        music_player.stop()


if __name__ == "__main__":
    main()
