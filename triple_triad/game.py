import argparse
import sys

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
from .synth.player import ChiptunePlayer
from .ui.cli import (
    choose_board_ui,
    choose_deck_mode_ui,
    choose_difficulty_ui,
    choose_rules_ui,
    loading_screen,
    main_menu,
    new_game_menu,
    options_menu,
    pause_message,
    quit_menu,
)
from .ui.display import print_banner, print_help


def run_single_or_tournament(is_tournament: bool) -> None:
    print_banner()

    difficulty = choose_difficulty_ui()
    ai_mode = get_cpu_ai_mode(difficulty)
    board_elements = choose_board_ui()

    if is_tournament:
        run_tournament(difficulty, ai_mode, board_elements)
        return

    rules = choose_rules_ui()
    print(f"\n  Active rules: {', '.join(sorted(rules)) if rules else 'None (Basic)'}")

    deck_choice = choose_deck_mode_ui()
    if deck_choice == "1":
        player_hand = choose_deck()
    elif deck_choice == "2":
        player_hand = build_starter_deck()
    elif deck_choice == "3":
        player_hand = build_random_deck()
    else:
        player_hand = choose_preset_deck()

    cpu_hand = build_cpu_deck(difficulty)

    for c in player_hand:
        c.owner = "P"
    for c in cpu_hand:
        c.owner = "CPU"

    print("\n  ── Your Deck ──")
    for c in player_hand:
        el = f"[{c.element}]" if c.element else ""
        print(
            f"    {c.name}{el}  ▲{c.top} ▶{c.right} ▼{c.bottom} ◀{c.left}  Lv{c.level}"
        )

    cfg = DIFFICULTY_CONFIG.get(difficulty)
    if cfg is None:
        print(f"\n  ERROR: Unknown difficulty '{difficulty}'")
        return
    print(
        f"\n  ── CPU Deck  (Lv {cfg['cpu_min_level']}-{cfg['cpu_max_level']}, AI: {ai_mode}) ──"
    )
    if ai_mode == "random":
        print("  Note: Random AI mode selected. Some card values may not be valid.")
    for c in cpu_hand:
        el = f"[{c.element}]" if c.element else ""
        print(
            f"    {c.name}{el}  ▲{c.top} ▶{c.right} ▼{c.bottom} ◀{c.left}  Lv{c.level}"
        )

    pause_message()
    run_game(player_hand, cpu_hand, rules, ai_mode, board_elements)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Triple Triad - Final Fantasy VIII card game", add_help=False
    )
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show game tutorial and help"
    )
    args = parser.parse_args()

    if args.help:
        print_help()
        sys.exit(0)

    music_player = ChiptunePlayer()
    music_on = False

    try:
        loading_screen()

        music_player.start()
        music_on = True

        while True:
            choice = main_menu()

            if choice == "new_game":
                ng = new_game_menu()
                if ng == "single":
                    run_single_or_tournament(False)
                elif ng == "tournament":
                    run_single_or_tournament(True)

            elif choice == "options":
                op = options_menu(music_on=music_on)
                if op == "toggle_music":
                    if music_on:
                        music_player.stop()
                        music_on = False
                    else:
                        music_player.start()
                        music_on = True

            elif choice == "quit":
                q = quit_menu()
                if q == "exit":
                    if music_on:
                        music_player.stop()
                    print("\nGoodbye!\n")
                    sys.exit(0)

    finally:
        music_player.stop()


if __name__ == "__main__":
    main()
