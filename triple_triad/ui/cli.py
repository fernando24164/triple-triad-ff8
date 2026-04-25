import random
import time

from blessed import Terminal

from ..constants import BOARD_CELLS
from ..data.cards import Element

term = Terminal()


def _center_x(text: str) -> int:
    return max(0, (term.width - len(text)) // 2)


def _draw_frame(title: str, subtitle: str = "") -> None:
    print(term.clear)
    print(term.move_yx(1, _center_x("TRIPLE TRIAD")) + term.bold_cyan("TRIPLE TRIAD"))
    print(term.move_yx(2, _center_x(title)) + term.cyan(title))
    if subtitle:
        print(term.move_yx(3, _center_x(subtitle)) + term.dim + subtitle)


def loading_screen(duration: float = 1.8, steps: int = 24) -> None:
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        for i in range(steps + 1):
            _draw_frame("Loading...")
            pct = i / steps
            bar_w = min(44, max(20, term.width // 3))
            fill = int(bar_w * pct)
            bar = "[" + "█" * fill + "·" * (bar_w - fill) + "]"
            pct_txt = f"{int(pct * 100):3d}%"

            y = term.height // 2
            print(term.move_yx(y, _center_x(bar)) + term.yellow(bar))
            print(term.move_yx(y + 2, _center_x(pct_txt)) + term.bold(pct_txt))
            time.sleep(duration / steps)


def selector(
    title: str,
    items: list[str],
    subtitle: str = "",
    help_text: str = "↑/↓ move • Enter select • q back",
) -> int | None:
    idx = 0
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            _draw_frame(title, subtitle)
            start_y = max(5, term.height // 2 - len(items) // 2)

            for i, item in enumerate(items):
                line = f"  {item}  "
                x = _center_x(line)
                if i == idx:
                    print(term.move_yx(start_y + i, x) + term.bold_black_on_cyan(line))
                else:
                    print(term.move_yx(start_y + i, x) + term.white(line))

            print(term.move_yx(term.height - 2, 2) + term.dim + help_text)

            k = term.inkey(timeout=0.2)
            if not k:
                continue
            if k.name == "KEY_UP":
                idx = (idx - 1) % len(items)
            elif k.name == "KEY_DOWN":
                idx = (idx + 1) % len(items)
            elif k.name == "KEY_ENTER" or k == "\n":
                return idx
            elif str(k).lower() == "q":
                return None


def multi_selector(
    title: str,
    options: list[tuple[str, str]],  # (id, label)
    preselected: list[str] | None = None,
    subtitle: str = "Space toggle • Enter confirm • q cancel",
) -> set[str] | None:
    selected = set(preselected or [])
    idx = 0

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            _draw_frame(title, subtitle)
            start_y = max(5, term.height // 2 - len(options) // 2)

            for i, (opt_id, label) in enumerate(options):
                mark = "✓" if opt_id in selected else " "
                line = f"[{mark}] {label}"
                x = _center_x(line)
                if i == idx:
                    print(term.move_yx(start_y + i, x) + term.bold_black_on_cyan(line))
                else:
                    print(term.move_yx(start_y + i, x) + term.white(line))

            k = term.inkey(timeout=0.2)
            if not k:
                continue
            if k.name == "KEY_UP":
                idx = (idx - 1) % len(options)
            elif k.name == "KEY_DOWN":
                idx = (idx + 1) % len(options)
            elif k == " ":
                opt_id = options[idx][0]
                if opt_id in selected:
                    selected.remove(opt_id)
                else:
                    selected.add(opt_id)
            elif k.name == "KEY_ENTER" or k == "\n":
                return selected
            elif str(k).lower() == "q":
                return None


# ── Top menus ────────────────────────────────────────────────────────────────


def main_menu() -> str:
    items = ["New Game", "Options", "Quit"]
    sel = selector("Main Menu", items, help_text="↑/↓ move • Enter select")
    if sel is None:
        return "quit"
    return ["new_game", "options", "quit"][sel]


def new_game_menu() -> str | None:
    items = ["Single Game", "Tournament", "Back"]
    sel = selector("New Game", items)
    if sel is None or sel == 2:
        return None
    return ["single", "tournament"][sel]


def options_menu(music_on: bool) -> str | None:
    music_label = "Mute Music" if music_on else "Continue Music"
    items = [music_label, "Back"]
    sel = selector("Options", items)
    if sel is None or sel == 1:
        return None
    return "toggle_music"


def quit_menu() -> str:
    items = ["Quit to Menu", "Quit Game"]
    sel = selector("Quit", items, help_text="↑/↓ move • Enter select")
    if sel is None or sel == 0:
        return "menu"
    return "exit"


# ── Game setup menus ─────────────────────────────────────────────────────────


def choose_difficulty_ui() -> str:
    # adjust labels if your engine supports more levels
    items = ["easy", "medium", "hard"]
    sel = selector(
        "Select Difficulty", items, subtitle="CPU deck strength + AI behavior"
    )
    if sel is None:
        return "Normal"
    return items[sel]


def choose_board_ui() -> list[Element | None]:
    items = ["None (no elemental cells)", "Random (0-2 random cells)"]
    sel = selector("Board Element Configuration", items)
    if sel is None or sel == 0:
        return [None] * BOARD_CELLS

    elements = list(Element)
    board: list[Element | None] = [None] * BOARD_CELLS
    n = random.randint(0, 2)
    for pos in random.sample(range(BOARD_CELLS), n):
        board[pos] = random.choice(elements)
    return board


def choose_rules_ui() -> set[str]:
    opts = [
        ("Open", "Open — See opponent's hand"),
        ("Same", "Same — Equal values on 2+ sides"),
        ("Plus", "Plus — Equal sums on 2+ sides"),
        ("Random", "Random — Cards dealt randomly"),
    ]
    chosen = multi_selector("Optional Rules", opts)
    return chosen or set()


def choose_deck_mode_ui() -> str:
    items = [
        "Choose your cards manually",
        "Random starter deck (Lv 1-3)",
        "Random deck (any level)",
        "Use a preset deck",
    ]
    sel = selector("Deck Selection", items)
    if sel is None:
        return "2"  # safe default
    return ["1", "2", "3", "4"][sel]


def pause_message(message: str = "Press Enter to continue...") -> None:
    with term.cbreak(), term.hidden_cursor():
        print("\n" + term.dim + message)
        while True:
            k = term.inkey(timeout=None)
            if k.name == "KEY_ENTER" or k == "\n":
                break
