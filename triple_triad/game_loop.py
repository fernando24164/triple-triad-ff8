import random

from .board import Board
from .rules import resolve_captures
from .ai import cpu_choose
from .ui import display_hand
from .scoring import calculate_scores, calculate_final_scores


def run_game(player_hand, cpu_hand, rules, ai_mode):
    """Run the full game loop until the board is full."""
    board = Board()
    first = random.choice(["P", "CPU"])
    print(f"\n  {'You go' if first == 'P' else 'CPU goes'} first!\n")

    turn = first
    turn_number = 1

    while any(board.is_empty(i) for i in range(9)):
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

    p_final, c_final = calculate_final_scores(board)
    print(f"\n  Final Score — You: {p_final}  CPU: {c_final}")

    if p_final > c_final:
        print("\n  🏆  YOU WIN!  Congratulations!")
    elif c_final > p_final:
        print("\n  💀  CPU WINS!  Better luck next time!")
    else:
        print("\n  🤝  IT'S A DRAW!")

    print()
