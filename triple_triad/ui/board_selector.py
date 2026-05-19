import random

from ..constants import BOARD_CELLS
from ..data.cards import Element


def choose_board() -> list[Element | None]:
    print("\n  ── Board Element Configuration ──")
    print("  [1] None - No element squares (default)")
    print("  [2] Random - Randomly assign elements to cells")

    choice = "1"
    try:
        choice = input("  Your choice [1/2]: ").strip()
        if choice not in ("1", "2"):
            print("  ✗ Enter 1 or 2.")
            choice = "1"
    except EOFError:
        pass

    if choice == "1":
        return [None] * BOARD_CELLS

    board: list[Element | None] = [None] * BOARD_CELLS
    num_elements = random.randint(0, 2)
    for pos in random.sample(range(BOARD_CELLS), num_elements):
        board[pos] = Element(random.choice(list(Element)))
    return board
