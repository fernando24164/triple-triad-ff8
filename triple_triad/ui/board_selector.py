import random

from ..constants import BOARD_CELLS
from ..data.cards import Element

BOARD_PRESETS = {
    "none": [None] * BOARD_CELLS,
    "random": None,
}


def choose_board() -> list[Element | None]:
    print("\n  ── Board Element Configuration ──")
    print("  [1] None - No element squares (default)")
    print("  [2] Random - Randomly assign elements to cells")

    choice = "1"
    try:
        choice = input("  Your choice [1/2/3/4/5]: ").strip()
        if choice not in ("1", "2", "3", "4", "5"):
            print("  ✗ Enter 1, 2, 3, 4, or 5.")
            choice = "1"
    except EOFError:
        pass

    if choice == "1":
        return BOARD_PRESETS["none"]
    elif choice == "2":
        elements = list(Element)
        board: list[Element | None] = [None] * BOARD_CELLS
        num_elements = random.randint(0, 2)
        positions = random.sample(range(BOARD_CELLS), num_elements)
        for pos in positions:
            board[pos] = random.choice(elements)
        return board
    else:
        # Fallback to none preset for any unhandled choice (3, 4, 5, etc.)
        return BOARD_PRESETS["none"]
