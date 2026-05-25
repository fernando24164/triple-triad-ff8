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
from .models.card import Card
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

    print("\n  ── Your Deck ──")
    for c in player_hand:
        el = f"[{c.element}]" if c.element else ""
        print(
            f"    {c.name}{el}  ▲{c.top} ▶{c.right} ▼{c.bottom} ◀{c.left}  Lv{c.level}"
        )

    cfg = DIFFICULTY_CONFIG[difficulty]
    print(
        f"\n  ── CPU Deck  (Lv {cfg['cpu_min_level']}-{cfg['cpu_max_level']}, "
        f"AI: {ai_mode}) ──"
    )
    for c in cpu_hand:
        el = f"[{c.element}]" if c.element else ""
        print(
            f"    {c.name}{el}  ▲{c.top} ▶{c.right} ▼{c.bottom} ◀{c.left}  Lv{c.level}"
        )

    run_game(player_hand, cpu_hand, rules, ai_mode, board_elements)
    pause_message()


def play_tournament() -> None:
    difficulty = choose_difficulty_ui()
    ai_mode = get_cpu_ai_mode(difficulty)
    board_elements = choose_board_ui()
    run_tournament(difficulty, ai_mode, board_elements)
    pause_message()


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
    args = parser.parse_args()

    if args.help:
        print_help()
        sys.exit(0)

    print_banner()

    music_player = ChiptunePlayer()
    music_on = not args.no_music
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
    finally:
        music_player.stop()


if __name__ == "__main__":
    main()
