from typing import Any

from blessed import Terminal

from ..constants import BOARD_CELLS
from ..data.cards import Element
from ..engine.rules import resolve_captures
from ..models.board import Board
from ..models.card import Card
from .dialogs import show_dialog
from .tutorial_text import SPEAKER, STEPS

term = Terminal()


def run_tutorial() -> None:
    """Run the full Queen of Cards tutorial."""
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        for step in STEPS:
            print(term.clear)
            ok = show_dialog(step["lines"], speaker=SPEAKER)
            if not ok:
                return

            handler = _INTERACTIVE.get(step["interactive"])
            if handler is not None:
                ok = handler()
                if not ok:
                    return

        _show_goodbye()


def _show_goodbye() -> None:
    """Final farewell screen."""
    print(term.clear)
    msg = "♕ Queen of Cards wishes you luck!"
    print(
        term.move_yx(term.height // 2, max(0, (term.width - term.length(msg)) // 2))
        + term.bold_cyan(msg)
    )
    msg2 = "Press any key to return to the main menu..."
    print(
        term.move_yx(
            term.height // 2 + 2, max(0, (term.width - term.length(msg2)) // 2)
        )
        + term.dim
        + msg2
    )
    term.inkey(timeout=None)


# ── Interactive demo handlers ────────────────────────────────────────────────


def _demo_place_card() -> bool:
    """Let the player place a card on an empty board."""
    board = Board()
    card = Card("Geezard")
    card.owner = "P"

    _draw_demo_frame("Step 1: Place a Card")
    _draw_board_demo(board)
    _draw_demo_text("Pick a position (1-9) to place your card!", y=5)

    key = _wait_for_position_choice(board)
    if key is None:
        return False
    pos = key

    board.place(pos, card)

    print(term.clear)
    _draw_demo_frame("Step 1: Place a Card")
    _draw_board_demo(board)
    _draw_demo_text(f"You placed Geezard at position {pos + 1}!", y=5)

    show_dialog(
        [
            "Excellent! Your card is now on the board.",
            "On your turn, you pick a card from your hand and a position. Simple!",
        ],
        speaker=SPEAKER,
    )
    return True


def _demo_capture() -> bool:
    """Let the player place a card to capture an opponent's card."""
    board = Board()
    cpu_card = Card("Bite Bug")
    cpu_card.owner = "CPU"
    board.place(0, cpu_card)

    player_card = Card("Geezard")
    player_card.owner = "P"

    _draw_demo_frame("Step 2: Capture!")
    _draw_board_demo(board)
    _draw_demo_text(
        "The CPU placed Bite Bug (Right=3). Place Geezard (Left=5)",
        y=4,
    )
    _draw_demo_text("at position 2 to capture it!", y=5)

    key = _wait_for_specific_key(1, board)
    if key is None:
        return False

    board.place(1, player_card)
    captures, events = resolve_captures(board, 1, player_card, [])

    for _, captured_card in captures:
        captured_card.owner = player_card.owner

    print(term.clear)
    _draw_demo_frame("Step 2: Capture!")
    _draw_board_demo(board)

    if captures:
        _draw_demo_text(
            "Your Left(5) beats CPU's Right(3) — you captured Bite Bug!",
            y=5,
        )
    else:
        _draw_demo_text("No capture happened. Try again!", y=5)

    show_dialog(
        [
            "That is how you capture cards! Place your card so that your touching value",
            "is higher than your opponent's. The captured card flips to your side.",
        ],
        speaker=SPEAKER,
    )
    return True


def _demo_element() -> bool:
    """Demonstrate element square bonuses."""
    elements: list[Element | None] = [None] * BOARD_CELLS
    elements[0] = Element.FIRE
    board = Board(elements=elements)

    cpu_card = Card("Red Bat")
    cpu_card.owner = "CPU"
    board.place(1, cpu_card)

    player_card = Card("Ruby Dragon")
    player_card.owner = "P"

    _draw_demo_frame("Step 3: Element Squares")
    _draw_board_demo(board)
    _draw_demo_text(
        "Position 1 is a Fire cell! Ruby Dragon is Fire-element.",
        y=4,
    )
    _draw_demo_text(
        "Without the bonus: Right(2) vs CPU's Left(2) → equal, no capture.",
        y=5,
    )
    _draw_demo_text(
        "With the +1 bonus: Right(3) > Left(2) → capture!",
        y=6,
    )
    _draw_demo_text("Press 1 to place Ruby Dragon on the Fire cell!", y=8)

    key = _wait_for_specific_key(0, board)
    if key is None:
        return False

    board.place(0, player_card)
    captures, events = resolve_captures(board, 0, player_card, [])

    for _, captured_card in captures:
        captured_card.owner = player_card.owner

    print(term.clear)
    _draw_demo_frame("Step 3: Element Squares")
    _draw_board_demo(board)

    if captures:
        _draw_demo_text(
            "The +1 Fire bonus made Right=3 > CPU's Left=2 → captured!",
            y=5,
        )
    else:
        _draw_demo_text(
            "No capture. The +1 bonus was not enough.",
            y=5,
        )

    show_dialog(
        [
            "Element squares give +1 to ALL sides of a matching-element card!",
            "Use them wisely to turn weak match-ups in your favour.",
        ],
        speaker=SPEAKER,
    )
    return True


_INTERACTIVE: dict[str, Any] = {
    "place_demo": _demo_place_card,
    "capture_demo": _demo_capture,
    "element_demo": _demo_element,
}


# ── Drawing helpers ──────────────────────────────────────────────────────────


def _draw_demo_frame(title: str) -> None:
    print(term.clear)
    print(
        term.move_yx(1, max(0, (term.width - term.length(title)) // 2))
        + term.bold_cyan(title)
    )


def _draw_board_demo(board: Board) -> None:
    board_str = board.display()
    lines = board_str.split("\n")
    start_y = max(8, (term.height - len(lines)) // 2)
    for i, line in enumerate(lines):
        x = max(0, (term.width - term.length(line)) // 2)
        print(term.move_yx(start_y + i, x) + term.normal + line)


def _draw_demo_text(text: str, y: int) -> None:
    x = max(0, (term.width - term.length(text)) // 2)
    print(term.move_yx(y, x) + term.white(text))


def _wait_for_position_choice(board: Board) -> int | None:
    """Wait for the player to press 1-9 for a valid empty position."""
    while True:
        k: Any = term.inkey(timeout=None)
        if str(k).lower() == "q":
            return None
        if k.isdigit():
            pos = int(k) - 1
            if 0 <= pos < BOARD_CELLS and board.is_empty(pos):
                return pos


def _wait_for_specific_key(expected_pos: int, board: Board) -> int | None:
    """Wait for the player to press the expected position key."""
    while True:
        k: Any = term.inkey(timeout=None)
        if str(k).lower() == "q":
            return None
        if k.isdigit():
            pos = int(k) - 1
            if pos == expected_pos:
                return pos
