import random
import time
from collections.abc import Collection

from blessed import Terminal

from ..ai.base import cpu_choose
from ..constants import BOARD_CELLS
from ..data.cards import Element
from ..models.board import Board
from ..models.card import Card
from ..ui.cli import pause_message
from ..ui.display import display_hand
from .rules import resolve_captures
from .scoring import calculate_final_scores, calculate_scores


def _decide_first() -> str:
    """Animate a bouncing selector between YOU and CPU, then reveal who goes first."""
    term = Terminal()
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
