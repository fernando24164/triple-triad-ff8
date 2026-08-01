from typing import Any

from blessed import Terminal

from ..constants import BOARD_CELLS
from ..data.cards import Element
from ..engine.rules import resolve_captures
from ..models.board import Board
from ..models.card import Card
from ..synth.sfx import play_cancel, play_confirm, play_cursor
from ..ui.position_selector import next_empty_in_direction
from .dialogs import show_dialog
from .tutorial_text import RULE_TOPIC_STEPS, SPEAKER, STEPS

term = Terminal()


def run_tutorial() -> None:
    """Run the full Queen of Cards tutorial."""
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        # Show welcome step
        ok = show_dialog(STEPS[0]["lines"], speaker=SPEAKER)
        if not ok:
            return

        # Rule selection loop
        if not _show_rule_selection():
            return

        # Remaining tutorial steps (goal, card stats, etc.)
        for step in STEPS[1:]:
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


def _show_rule_selection() -> bool:
    """Show a rule topic selection menu, loop until user skips or quits."""
    topic_keys = list(RULE_TOPIC_STEPS.keys())

    while True:
        topic_labels = [RULE_TOPIC_STEPS[k]["lines"][0] for k in topic_keys]
        topic_labels.append("Skip — continue without deep-dive")
        idx = _selector_menu("Choose a Rule to Explore", topic_labels)

        if idx is None:
            return False

        if idx >= len(topic_keys):
            return True

        topic = topic_keys[idx]
        data = RULE_TOPIC_STEPS[topic]

        print(term.clear)
        ok = show_dialog(data["lines"], speaker=SPEAKER)
        if not ok:
            return False

        handler = _INTERACTIVE.get(data["interactive"])
        if handler is not None:
            ok = handler()
            if not ok:
                return False


# ── Rule selection menu ──────────────────────────────────────────────


def _selector_menu(title: str, items: list[str]) -> int | None:
    """Display a navigable selector menu (no fullscreen — outer context handles it).

    Returns chosen index or None.
    """
    idx = 0
    while True:
        print(term.clear)
        print(
            term.move_yx(1, max(0, (term.width - term.length(title)) // 2))
            + term.bold_cyan(title)
        )
        start_y = max(4, term.height // 2 - len(items) // 2)
        for i, item in enumerate(items):
            line = f"  {item}  "
            x = max(0, (term.width - len(line)) // 2)
            y = start_y + i
            if i == idx:
                print(term.move_yx(y, x) + term.bold_black_on_cyan(line))
            else:
                print(term.move_yx(y, x) + term.white(line))
        print(
            term.move_yx(term.height - 2, 2)
            + term.dim
            + "↑/↓ move • Enter select • q to cancel"
        )
        k = term.inkey(timeout=0.1)
        if not k:
            continue
        if str(k).lower() == "q":
            play_cancel()
            return None
        if k.name == "KEY_UP":
            idx = (idx - 1) % len(items)
            play_cursor()
        elif k.name == "KEY_DOWN":
            idx = (idx + 1) % len(items)
            play_cursor()
        elif k.name == "KEY_ENTER" or k == "\n":
            play_confirm()
            return idx


# ── Deep-dive interactive demos ──────────────────────────────────────


def _demo_same() -> bool:
    """Demonstrate the Same rule."""
    # Mesmerize (bottom=3) at pos 1, Thrustaevis (right=3) at pos 3
    cpu1 = Card("Mesmerize")
    cpu1.owner = "CPU"
    cpu2 = Card("Thrustaevis")
    cpu2.owner = "CPU"
    board = Board()
    board.place(1, cpu1)
    board.place(3, cpu2)

    player = Card("Belhelmel")
    player.owner = "P"

    _draw_demo_frame("Same Rule")
    _draw_board_demo(board)
    _draw_demo_text(
        "Mesmerize bottom=3 — Thrustaevis right=3",
        y=4,
    )
    _draw_demo_text("Place Same card with top=3 & left=3 at pos 5!", y=5)
    _draw_demo_text("Press 5 to place Belhelmel at the center!", y=7)

    key = _wait_for_specific_key(4, board)  # pos 5 = index 4
    if key is None:
        return False

    board.place(4, player)
    captures, events = resolve_captures(board, 4, player, ["Same"])
    for _, c in captures:
        c.owner = player.owner

    print(term.clear)
    _draw_demo_frame("Same Rule")
    _draw_board_demo(board)

    if "Same" in events:
        _draw_demo_text(
            f"Same triggered! {len(captures)} cards captured!",
            y=5,
        )
    else:
        _draw_demo_text("Same did not trigger. Check values.", y=5)

    show_dialog(
        [
            "Same Rule: If 2+ sides of your placed card match the",
            "touching opponent values exactly, capture ALL adjacent!",
        ],
        speaker=SPEAKER,
    )
    return True


def _demo_same_wall() -> bool:
    """Demonstrate Same Wall (board edges count as rank A)."""
    cpu = Card("Gayla")
    cpu.owner = "CPU"
    board = Board()
    board.place(4, cpu)

    player = Card("Bahamut")
    player.owner = "P"

    _draw_demo_frame("Same Wall")
    _draw_board_demo(board)
    _draw_demo_text("Gayla [CPU] is at the center (pos 5).", y=4)
    _draw_demo_text("Your Bahamut top=10 matches the board edge (rank A)!", y=5)
    _draw_demo_text("And bottom=2 matches Gayla top=2 — that's 2 matches.", y=6)
    _draw_demo_text("Press 2 to place Bahamut at the top edge!", y=8)

    key = _wait_for_specific_key(1, board)  # pos 2 = index 1
    if key is None:
        return False

    board.place(1, player)
    captures, events = resolve_captures(board, 1, player, {"Same", "Same Wall"})
    for _, c in captures:
        c.owner = player.owner

    print(term.clear)
    _draw_demo_frame("Same Wall")
    _draw_board_demo(board)

    if "Same" in events:
        _draw_demo_text(
            f"Same Wall triggered via edge + match! {len(captures)} captured!",
            y=5,
        )
    else:
        _draw_demo_text("Same did not trigger.", y=5)

    show_dialog(
        [
            "Same Wall: Board edges count as rank A (10) toward",
            "the Same rule's 2+ match requirement. Very powerful",
            "on corner and edge cells!",
        ],
        speaker=SPEAKER,
    )
    return True


def _demo_plus() -> bool:
    """Demonstrate the Plus rule."""
    opp1 = Card("Grat")
    opp1.owner = "CPU"
    opp2 = Card("Red Bat")
    opp2.owner = "CPU"
    board = Board()
    board.place(1, opp1)
    board.place(3, opp2)

    player = Card("Gayla")
    player.owner = "P"

    _draw_demo_frame("Plus Rule")
    _draw_board_demo(board)
    _draw_demo_text("Gayla  [T:2  R:1  B:4  L:4]", y=4)
    _draw_demo_text(
        "Top(2) + Grat bottom(3) = 5",
        y=5,
    )
    _draw_demo_text(
        "Left(4) + Red Bat right(1) = 5",
        y=6,
    )
    _draw_demo_text("Equal sums on 2 sides → Plus triggers!", y=7)
    _draw_demo_text("Press 5 to place Gayla at the center!", y=9)

    key = _wait_for_specific_key(4, board)
    if key is None:
        return False

    board.place(4, player)
    captures, events = resolve_captures(board, 4, player, ["Plus"])
    for _, c in captures:
        c.owner = player.owner

    print(term.clear)
    _draw_demo_frame("Plus Rule")
    _draw_board_demo(board)

    if "Plus" in events:
        _draw_demo_text(
            f"Plus triggered! {len(captures)} cards captured!",
            y=5,
        )
    else:
        _draw_demo_text("Plus did not trigger. Check sums.", y=5)

    show_dialog(
        [
            "Plus Rule: If the sums of your card's value + adjacent",
            "opponent's value are equal on 2+ sides, capture them all!",
        ],
        speaker=SPEAKER,
    )
    return True


def _demo_combo() -> bool:
    """Demonstrate the Combo chain reaction."""
    board = Board()
    opp1 = Card("Mesmerize")
    opp1.owner = "CPU"
    opp2 = Card("Thrustaevis")
    opp2.owner = "CPU"
    opp3 = Card("Grat")
    opp3.owner = "CPU"
    opp4 = Card("Geezard")
    opp4.owner = "CPU"
    board.place(1, opp1)
    board.place(3, opp2)
    board.place(0, opp3)
    board.place(6, opp4)

    player = Card("Belhelmel")
    player.owner = "P"

    _draw_demo_frame("Combo Rule")
    _draw_board_demo(board)
    _draw_demo_text(
        "Belhelmel top=3 matches Mesmerize bottom=3",
        y=4,
    )
    _draw_demo_text(
        "Belhelmel left=3 matches Thrustaevis right=3",
        y=5,
    )
    _draw_demo_text("Same triggers — then Combo chain-captures!", y=6)
    _draw_demo_text("Press 5 to place Belhelmel at center!", y=8)

    key = _wait_for_specific_key(4, board)
    if key is None:
        return False

    board.place(4, player)
    captures, events = resolve_captures(board, 4, player, ["Same"])
    for _, c in captures:
        c.owner = player.owner

    print(term.clear)
    _draw_demo_frame("Combo Rule")
    _draw_board_demo(board)

    combo_label = "Combo" in events
    if cap := (len(captures) if combo_label else 0):
        _draw_demo_text(
            f"Same + Combo! {cap} cards captured in chain!",
            y=5,
        )
    else:
        _draw_demo_text("Same triggered but no chain reaction.", y=5)

    show_dialog(
        [
            "Combo: When Same/Plus triggers, every flipped card",
            "automatically chain-captures its neighbors via the",
            "basic (higher-value-wins) rule. Can wipe the board!",
        ],
        speaker=SPEAKER,
    )
    return True


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

    cur = 0
    while True:
        _draw_demo_frame("Step 1: Place a Card")
        _draw_board_demo(board, highlight=cur)
        _draw_demo_text("Arrow keys move • Enter to place • q to quit", y=5)

        k: Any = term.inkey(timeout=None)
        if str(k).lower() == "q":
            return False
        if k.name in ("KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"):
            nxt = next_empty_in_direction(board, cur, k.name)
            if nxt is not None:
                cur = nxt
                play_cursor()
        elif k.name == "KEY_ENTER" or k == "\n":
            play_confirm()
            break
        elif k.isdigit():
            num = int(k) - 1
            if 0 <= num < BOARD_CELLS and board.is_empty(num):
                play_confirm()
                cur = num
                break

    pos = cur

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
    "same_demo": _demo_same,
    "same_wall_demo": _demo_same_wall,
    "plus_demo": _demo_plus,
    "combo_demo": _demo_combo,
}


# ── Drawing helpers ──────────────────────────────────────────────────────────


def _draw_demo_frame(title: str) -> None:
    print(term.clear)
    print(
        term.move_yx(1, max(0, (term.width - term.length(title)) // 2))
        + term.bold_cyan(title)
    )


def _draw_board_demo(board: Board, highlight: int | None = None) -> None:
    board_str = board.display(highlight=highlight)
    lines = board_str.split("\n")
    start_y = max(8, (term.height - len(lines)) // 2)
    for i, line in enumerate(lines):
        x = max(0, (term.width - term.length(line)) // 2)
        print(term.move_yx(start_y + i, x) + term.normal + line)


def _draw_demo_text(text: str, y: int) -> None:
    x = max(0, (term.width - term.length(text)) // 2)
    print(term.move_yx(y, x) + term.white(text))


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
