from .deck.builder import (
    DIFFICULTY_CONFIG,
    build_cpu_deck,
    build_random_deck,
    build_starter_deck,
    get_cpu_ai_mode,
)
from .deck.deck_selector import choose_preset_deck
from .deck.picker import choose_deck
from .engine.difficulty_selector import choose_difficulty
from .engine.game_loop import run_game
from .synth.player import ChiptunePlayer
from .ui.display import choose_rules, print_banner


def main():
    print_banner()

    # ── Start background music ─────────────────────────────────────────────
    music_player = ChiptunePlayer()
    try:
        music_player.start()

        # ── Difficulty ─────────────────────────────────────────────────────────
        difficulty = choose_difficulty()
        ai_mode = get_cpu_ai_mode(difficulty)

        # ── Rules ──────────────────────────────────────────────────────────────
        rules = choose_rules()
        print(f"\n  Active rules: {', '.join(rules) if rules else 'None (Basic)'}")

        # ── Deck selection ─────────────────────────────────────────────────────
        print("\n  ── Deck Selection ──")
        print("  [1] Choose your cards manually")
        print("  [2] Random starter deck (Lv 1-3)")
        print("  [3] Random deck (any level)")
        print("  [4] Use a preset deck")
        while True:
            deck_choice = input("  Your choice [1/2/3/4]: ").strip()
            if deck_choice in ("1", "2", "3", "4"):
                break
            print("  ✗ Enter 1, 2, 3, or 4.")

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

        # ── Print both decks so the player can see the matchup ─────────────────
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

        # ── Play ───────────────────────────────────────────────────────────────
        run_game(player_hand, cpu_hand, rules, ai_mode)

    finally:
        music_player.stop()


if __name__ == "__main__":
    main()
