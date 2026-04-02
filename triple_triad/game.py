# triple_triad/game.py
import random

from .board import Board
from .rules import resolve_captures
from .ai import cpu_choose
from .deck import (
    build_starter_deck,
    build_cpu_deck,
    build_random_deck,
    build_preset_deck,
    choose_deck,
    get_cpu_ai_mode,
    list_presets,
    DIFFICULTY_CONFIG,
)
from .ui import display_hand, print_banner, choose_rules
from .synth.player import ChiptunePlayer


def _choose_difficulty() -> str:
    """Prompt the player to pick a difficulty and show what it means."""
    print("\n  ── Difficulty ──")
    options = [
        ("1", "easy"),
        ("2", "medium"),
        ("3", "hard"),
    ]
    for key, diff in options:
        cfg = DIFFICULTY_CONFIG[diff]
        print(f"  [{key}] {diff.capitalize():<8} — {cfg['description']}")

    diff_map = {key: diff for key, diff in options}
    while True:
        choice = input("\n  Choose difficulty [1/2/3]: ").strip()
        if choice in diff_map:
            selected = diff_map[choice]
            print(f"\n  ✓ Difficulty set to: {selected.upper()}")
            return selected
        print("  ✗ Please enter 1, 2, or 3.")


def _choose_preset_deck() -> list:
    """Prompt the player to pick a preset deck and return the cards."""
    presets = list_presets()
    print("\n  ── Preset Decks ──")
    for i, name in enumerate(presets, 1):
        cards = build_preset_deck(name)
        card_summary = ", ".join(c.name for c in cards[:3])
        if len(cards) > 3:
            card_summary += f" +{len(cards) - 3} more"
        print(f"  [{i}] {name:<16} — {card_summary}")

    while True:
        try:
            choice = int(input(f"\n  Choose preset [1-{len(presets)}]: ").strip())
            if 1 <= choice <= len(presets):
                selected = presets[choice - 1]
                deck = build_preset_deck(selected)
                print(f"\n  ✓ Selected: {selected.upper()}")
                return deck
            print(f"  ✗ Enter a number between 1 and {len(presets)}.")
        except ValueError:
            print("  ✗ Enter a number.")


def main():
    print_banner()

    # ── Start background music ─────────────────────────────────────────────
    music_player = ChiptunePlayer()
    try:
        music_player.start()

        # ── Difficulty ─────────────────────────────────────────────────────────
        difficulty = _choose_difficulty()
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
            player_hand = _choose_preset_deck()
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

        # ── First turn ─────────────────────────────────────────────────────────
        first = random.choice(["P", "CPU"])
        print(f"\n  {'You go' if first == 'P' else 'CPU goes'} first!\n")

        board = Board()
        turn = first
        turn_number = 1

        while any(board.is_empty(i) for i in range(9)):
            print("\n" + "═" * 62)
            print(f"  Turn {turn_number}  |  {'YOUR TURN' if turn == 'P' else 'CPU TURN'}")
            print("═" * 62)
            print(board.display())

            # ── Score ──────────────────────────────────────────────────────────
            p_score = sum(1 for c in board.cells if c and c.owner == "P") + sum(
                1 for c in player_hand
            )
            c_score = sum(1 for c in board.cells if c and c.owner == "CPU") + sum(
                1 for c in cpu_hand
            )
            print(f"\n  Score — You: {p_score}  CPU: {c_score}")

            if turn == "P":
                show_cpu = "Open" in rules
                display_hand(player_hand, "Your")
                display_hand(cpu_hand, "CPU", show=show_cpu)

                # Pick card
                while True:
                    try:
                        ci = int(input(f"\n  Choose card (1-{len(player_hand)}): ")) - 1
                        if 0 <= ci < len(player_hand):
                            break
                        print(f"  ✗ Enter a number between 1 and {len(player_hand)}.")
                    except ValueError:
                        print("  ✗ Enter a number.")

                # Pick position
                empty = [i for i in range(9) if board.is_empty(i)]
                while True:
                    try:
                        pos = int(input("  Choose position (1-9): ")) - 1
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
                ci, pos = cpu_choose(board, cpu_hand, rules, mode=ai_mode)
                card = cpu_hand.pop(ci)
                card.owner = "CPU"
                board.place(pos, card)
                print(f"  CPU placed [{card.name}] at position {pos + 1}")

            # ── Captures ───────────────────────────────────────────────────────
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

        # ── Game over ──────────────────────────────────────────────────────────
        print("\n" + "═" * 62)
        print("  GAME OVER")
        print("═" * 62)
        print(board.display())

        p_final = sum(1 for c in board.cells if c and c.owner == "P")
        c_final = sum(1 for c in board.cells if c and c.owner == "CPU")

        print(f"\n  Final Score — You: {p_final}  CPU: {c_final}")

        if p_final > c_final:
            print("\n  🏆  YOU WIN!  Congratulations!")
        elif c_final > p_final:
            print("\n  💀  CPU WINS!  Better luck next time!")
        else:
            print("\n  🤝  IT'S A DRAW!")

        print()
    
    finally:
        music_player.stop()


if __name__ == "__main__":
    main()