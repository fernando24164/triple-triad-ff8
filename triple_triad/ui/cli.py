import random
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from blessed import Terminal

from ..constants import BOARD_CELLS
from ..data.cards import Element
from ..models.card import Card
from ..synth.constants import MUSIC_VOLUME_LEVELS
from ..synth.sfx import play_cancel, play_confirm, play_cursor

term = Terminal()

TITLE_ART = [
    "╔══════════════════════════════════════════════════════════╗",
    "║          TRIPLE TRIAD  —  Final Fantasy VIII             ║",
    "║                       Text Edition                       ║",
    "╚══════════════════════════════════════════════════════════╝",
]


def _center_x(text: str) -> int:
    return max(0, (term.width - len(text)) // 2)


def _draw_frame(title: str, subtitle: str = "") -> None:
    print(term.clear)
    print(term.move_yx(1, _center_x("TRIPLE TRIAD")) + term.bold_cyan("TRIPLE TRIAD"))
    print(term.move_yx(2, _center_x(title)) + term.cyan(title))
    if subtitle:
        print(term.move_yx(3, _center_x(subtitle)) + term.dim + subtitle)


def _clear_row(y: int) -> str:
    """Escape sequence to blank a single row without touching the rest of
    the screen — avoids the full-screen clear+repaint flash on redraw."""
    return term.move_yx(y, 0) + term.clear_eol


def _screen_border() -> None:
    w, h = term.width, term.height
    c = term.cyan
    parts = [
        term.move_yx(0, 0) + c + "╔" + "═" * (w - 2) + "╗",
    ]
    for y in range(1, h - 1):
        parts.append(term.move_yx(y, 0) + c + "║")
        parts.append(term.move_yx(y, w - 1) + c + "║")
    parts.append(term.move_yx(h - 1, 0) + c + "╚" + "═" * (w - 2) + "╝")
    print("".join(parts), end="")


def _animate_title() -> None:
    """Drop the title art into place, then settle with a small bounce.
    Clears once up front and draws the static border once — every frame
    after that only erases the title's previous row positions and repaints
    it at the new ones, so the screen doesn't flash on every frame."""
    title_h = len(TITLE_ART)
    final_y = 2
    start_y = -title_h - 2
    frames = 30

    print(term.clear, end="")
    _screen_border()

    prev_y: int | None = None

    def paint(y: int) -> None:
        nonlocal prev_y
        out = []
        if prev_y is not None:
            for row, line in enumerate(TITLE_ART):
                screen_y = prev_y + row
                if 0 <= screen_y < term.height:
                    out.append(
                        term.move_yx(screen_y, _center_x(line)) + " " * len(line)
                    )
        for row, line in enumerate(TITLE_ART):
            screen_y = y + row
            if 0 <= screen_y < term.height:
                out.append(
                    term.normal
                    + term.move_yx(screen_y, _center_x(line))
                    + term.bold_cyan(line)
                )
        print("".join(out), end="", flush=True)
        prev_y = y

    for i in range(frames + 1):
        t = i / frames
        eased = 1 - (1 - t) * (1 - t) * (1 - t)
        y = int(start_y + (final_y - start_y) * eased)
        paint(y)
        time.sleep(0.025)

    for extra, delay in ((3, 0.06), (2, 0.05), (1, 0.04), (0, 0)):
        paint(final_y + extra)
        time.sleep(delay)


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


class _MenuBase:
    def __init__(
        self,
        title: str,
        help_text: str = "↑/↓ move • Enter select • q back",
        subtitle: str = "",
    ) -> None:
        self.title = title
        self.help_text = help_text
        self.subtitle = subtitle
        self.idx = 0

    def item_count(self) -> int:
        raise NotImplementedError

    def draw_items(self) -> None:
        raise NotImplementedError

    def on_enter(self) -> int | set[str] | str | None:
        raise NotImplementedError

    def on_quit(self) -> int | set[str] | str | None:
        return None

    def on_left(self) -> None:
        pass

    def on_right(self) -> None:
        pass

    def draw(self) -> None:
        _draw_frame(self.title, self.subtitle)

    def handle_key(self, k: Any) -> int | set[str] | str | None:
        if k.name == "KEY_UP":
            self.idx = (self.idx - 1) % self.item_count()
            play_cursor()
        elif k.name == "KEY_DOWN":
            self.idx = (self.idx + 1) % self.item_count()
            play_cursor()
        elif k.name == "KEY_LEFT":
            self.on_left()
        elif k.name == "KEY_RIGHT":
            self.on_right()
        elif k.name == "KEY_ENTER" or k == "\n":
            play_confirm()
            return self.on_enter()
        return None

    def run(self, manage_screen: bool = True) -> int | set[str] | str | None:
        @contextmanager
        def _noop() -> Iterator[None]:
            yield

        screen = term.fullscreen() if manage_screen else _noop()
        cbreak = term.cbreak() if manage_screen else _noop()
        hidden = term.hidden_cursor() if manage_screen else _noop()

        # Frame + help text are static for the life of this menu, so they
        # only need to be painted once — only draw_items() (below) runs
        # on every keypress, to avoid a full-screen clear/flash per move.
        with screen, cbreak, hidden:
            self.draw()
            self.draw_items()
            print(term.move_yx(term.height - 2, 2) + term.dim + self.help_text)

            while True:
                k = term.inkey(timeout=0.2)
                if not k:
                    continue
                if str(k).lower() == "q":
                    play_cancel()
                    return self.on_quit()
                result = self.handle_key(k)
                if result is not None:
                    return result
                self.draw_items()


class _SelectorMenu(_MenuBase):
    def __init__(
        self,
        title: str,
        items: list[str],
        subtitle: str = "",
        help_text: str = "↑/↓ move • Enter select • q back",
        start_idx: int = 0,
    ) -> None:
        super().__init__(title, help_text, subtitle)
        self.items = items
        self.idx = start_idx if 0 <= start_idx < len(items) else 0

    def item_count(self) -> int:
        return len(self.items)

    def draw_items(self) -> None:
        start_y = max(5, term.height // 2 - len(self.items) // 2)
        out = []
        for i, item in enumerate(self.items):
            line = f"  {item}  "
            x = _center_x(line)
            y = start_y + i
            style = term.bold_black_on_cyan if i == self.idx else term.white
            out.append(_clear_row(y) + term.move_yx(y, x) + style(line))
        print("".join(out), end="", flush=True)

    def on_enter(self) -> int:
        return self.idx

    def on_quit(self) -> None:
        return None


class _MultiSelectorMenu(_MenuBase):
    def __init__(
        self,
        title: str,
        options: list[tuple[str, str]],
        preselected: list[str] | None = None,
        subtitle: str = "Space toggle • Enter confirm • q cancel",
    ) -> None:
        super().__init__(title, subtitle=subtitle)
        self.options = options
        self.selected = set(preselected or [])

    def item_count(self) -> int:
        return len(self.options)

    def draw_items(self) -> None:
        start_y = max(5, term.height // 2 - len(self.options) // 2)
        out = []
        for i, (opt_id, label) in enumerate(self.options):
            mark = "✓" if opt_id in self.selected else " "
            line = f"[{mark}] {label}"
            x = _center_x(line)
            y = start_y + i
            style = term.bold_black_on_cyan if i == self.idx else term.white
            out.append(_clear_row(y) + term.move_yx(y, x) + style(line))
        print("".join(out), end="", flush=True)

    def handle_key(self, k: Any) -> set[str] | None:
        if k == " ":
            opt_id = self.options[self.idx][0]
            if opt_id in self.selected:
                self.selected.remove(opt_id)
            else:
                self.selected.add(opt_id)
            return None
        result = super().handle_key(k)
        return result  # type: ignore[return-value]

    def on_enter(self) -> set[str]:
        return self.selected

    def on_quit(self) -> None:
        return None


def selector(
    title: str,
    items: list[str],
    subtitle: str = "",
    help_text: str = "↑/↓ move • Enter select • q back",
    start_idx: int = 0,
) -> int | None:
    result = _SelectorMenu(title, items, subtitle, help_text, start_idx).run()
    return result  # type: ignore[return-value]


def selector_embedded(title: str, items: list[str]) -> int | None:
    """Like ``selector`` but without managing the terminal screen — for use
    inside an already-active fullscreen context."""
    result = _SelectorMenu(title, items).run(manage_screen=False)
    return result  # type: ignore[return-value]


def multi_selector(
    title: str,
    options: list[tuple[str, str]],
    preselected: list[str] | None = None,
    subtitle: str = "Space toggle • Enter confirm • q cancel",
) -> set[str] | None:
    result = _MultiSelectorMenu(title, options, preselected, subtitle).run()
    return result  # type: ignore[return-value]


# ── Top menus ────────────────────────────────────────────────────────────────


class _MainMenu(_MenuBase):
    """Main menu, drawn below the animated title art."""

    ACTIONS = ["new_game", "deck_manager", "tutorial", "options", "quit"]
    ITEMS = ["New Game", "Deck Manager", "Tutorial", "Options", "Quit"]

    def __init__(self) -> None:
        super().__init__("TRIPLE TRIAD")
        self.items_y = 0

    def item_count(self) -> int:
        return len(self.ITEMS)

    def draw(self) -> None:
        # Border and title art never change during this menu's lifetime,
        # and _animate_title() already left them painted at their final
        # position — re-clearing and redrawing them here just caused a
        # visible flash right as the title-drop animation finished. Only
        # the help text (not drawn by the animation) still needs adding.
        avail = term.height - (2 + len(TITLE_ART))
        self.items_y = 2 + len(TITLE_ART) + (avail - len(self.ITEMS)) // 2
        help_text = "↑/↓ move • Enter select"
        print(
            term.normal
            + term.move_yx(term.height - 2, _center_x(help_text))
            + term.dim
            + help_text,
            end="",
            flush=True,
        )

    def draw_items(self) -> None:
        out = []
        for i, item in enumerate(self.ITEMS):
            line = f"  {item}  "
            x = _center_x(line)
            y = self.items_y + i
            style = term.bold_black_on_cyan if i == self.idx else term.white
            out.append(
                term.normal + _clear_row(y) + term.move_yx(y, x) + style(line)
            )
        print("".join(out), end="", flush=True)

    def on_enter(self) -> str:
        return self.ACTIONS[self.idx]

    def on_quit(self) -> str:
        return "quit"


def main_menu() -> str:
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        _animate_title()
        result = _MainMenu().run(manage_screen=False)
        if isinstance(result, str):
            return result
        return "quit"


class _OptionsMenu(_MenuBase):
    """Interactive options screen: toggle music and adjust its intensity."""

    def __init__(self, music_player: Any, volume_idx: int) -> None:
        super().__init__(
            "Options",
            help_text="↑/↓ move • ←/→ adjust volume • Enter select • q back",
        )
        self.music_player = music_player
        self.volume_idx = volume_idx

    def item_count(self) -> int:
        return 3

    def _labels(self) -> list[str]:
        music_on = self.music_player.is_playing()
        vol_name, _ = MUSIC_VOLUME_LEVELS[self.volume_idx]
        return [
            "Mute Music" if music_on else "Start Music",
            f"Music Volume:  ◀ {vol_name} ▶",
            "Back",
        ]

    def draw_items(self) -> None:
        labels = self._labels()
        start_y = max(5, term.height // 2 - len(labels) // 2)
        out = []
        for i, label in enumerate(labels):
            line = f"  {label}  "
            x = _center_x(line)
            y = start_y + i
            style = term.bold_black_on_cyan if i == self.idx else term.white
            out.append(_clear_row(y) + term.move_yx(y, x) + style(line))
        print("".join(out), end="", flush=True)

    def _adjust_volume(self, step: int) -> None:
        new_idx = self.volume_idx + step
        if 0 <= new_idx < len(MUSIC_VOLUME_LEVELS):
            self.volume_idx = new_idx
            self.music_player.set_volume(MUSIC_VOLUME_LEVELS[new_idx][1])
            play_cursor()

    def on_left(self) -> None:
        if self.idx == 1:
            self._adjust_volume(-1)

    def on_right(self) -> None:
        if self.idx == 1:
            self._adjust_volume(1)

    def on_enter(self) -> int | None:
        if self.idx == 0:
            if self.music_player.is_playing():
                self.music_player.stop()
            else:
                self.music_player.start()
            return None
        if self.idx == 2:
            return self.volume_idx
        return None

    def on_quit(self) -> int:
        return self.volume_idx


def options_menu(music_player: Any, volume_idx: int) -> int:
    """Interactive options screen. Music on/off and volume changes are
    applied live to ``music_player``; returns the resulting volume index so
    callers can carry it into the next visit."""
    result = _OptionsMenu(music_player, volume_idx).run()
    return result if isinstance(result, int) else volume_idx


def new_game_menu() -> str | None:
    items = ["Single Game", "Tournament", "Multiplayer", "Back"]
    sel = selector("New Game", items)
    if sel is None or sel == 3:
        return None
    return ["single", "tournament", "multiplayer"][sel]


def deck_manager_ui() -> None:
    from ..deck.picker import choose_deck
    from ..deck.shelf import delete_deck, list_decks, load_deck

    while True:
        items = ["Create a new deck", "View / Delete saved decks", "Back"]
        sel = selector("Deck Manager", items)
        if sel is None or sel == 2:
            return

        if sel == 0:
            picked = choose_deck()
            if picked:
                prompt_save_deck_ui(picked)

        elif sel == 1:
            saved = list_decks()
            if not saved:
                print("\n  No saved decks found. Create one first.")
                pause_message()
                continue

            view_items = [
                f"{name} ({len(load_deck(name) or [])} cards)" for name in saved
            ] + ["Back"]
            sel2 = selector("Saved Decks — select to view", view_items)
            if sel2 is None or sel2 >= len(saved):
                continue

            name = saved[sel2]
            loaded = load_deck(name)
            if loaded is None:
                print(f"\n  ✗ Could not load '{name}'.")
                pause_message()
                continue

            print(f"\n  ── {name} ──")
            for c in loaded:
                el = f"[{c.element}]" if c.element else ""
                print(
                    f"    {c.name}{el}  ▲{c.top} ▶{c.right} ▼{c.bottom} ◀{c.left}  Lv{c.level}"
                )

            confirm = input("\n  Delete this deck? (y/n/q): ").strip().lower()
            if confirm == "q":
                continue
            if confirm.startswith("y"):
                delete_deck(name)
                print(f"  ✓ Deck '{name}' deleted.")
            pause_message()


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

    board: list[Element | None] = [None] * BOARD_CELLS
    n = random.randint(0, 2)
    for pos in random.sample(range(BOARD_CELLS), n):
        board[pos] = Element(random.choice(list(Element)))
    return board


def choose_rules_ui() -> set[str]:
    opts = [
        ("Open", "Open — See opponent's hand"),
        ("Same", "Same — Equal values on 2+ sides"),
        ("Same Wall", "Same Wall — Board edges count as rank A for Same"),
        ("Plus", "Plus — Equal sums on 2+ sides"),
        ("Random", "Random — Cards dealt randomly"),
    ]
    chosen = multi_selector("Optional Rules", opts)
    return chosen or set()


def choose_deck_mode_ui() -> str | None:
    items = [
        "Choose your cards manually",
        "Random starter deck (Lv 1-3)",
        "Random deck (any level)",
        "Use a preset deck",
        "Load a saved deck",
    ]
    sel = selector("Deck Selection", items)
    if sel is None:
        return None
    return ["1", "2", "3", "4", "5"][sel]


def choose_saved_deck_ui() -> list[Card] | None:
    from ..deck.shelf import delete_deck, list_decks, load_deck

    saved = list_decks()
    if not saved:
        print("\n  No saved decks found. Build and save one via manual pick first.")
        pause_message()
        return None

    print("\n  ── Saved Decks ──")
    for i, name in enumerate(saved, 1):
        deck = load_deck(name)
        if deck:
            summary = ", ".join(c.name for c in deck[:2])
            summary += f" +{len(deck) - 2} more"
            print(f"  [{i}] {name:<20} — {summary}")
        else:
            print(f"  [{i}] {name:<20} — (invalid)")

    print("  [d] Delete a deck")
    print("  [0] Back")
    print("  [q] Back to menu")

    while True:
        choice = input(f"\n  Choose a deck [0-{len(saved)}/d/q]: ").strip().lower()
        if choice == "0" or choice == "q":
            return None
        if choice == "d":
            print("\n  ── Delete a Deck ──")
            for i, name in enumerate(saved, 1):
                print(f"  [{i}] {name}")
            print("  [0] Cancel")
            print("  [q] Back")
            del_choice = (
                input(f"  Choose deck to delete [0-{len(saved)}/q]: ").strip().lower()
            )
            if del_choice == "q":
                continue
            try:
                idx = int(del_choice) - 1
                if 0 <= idx < len(saved):
                    confirm = input(f"  Delete '{saved[idx]}'? (y/n): ").strip().lower()
                    if confirm.startswith("y"):
                        delete_deck(saved[idx])
                        print(f"  ✓ Deck '{saved[idx]}' deleted.")
                        saved = list_decks()
                        if not saved:
                            print("  No decks remaining.")
                            return None
                        continue
                    else:
                        print("  Deletion cancelled.")
            except ValueError:
                pass
            print("  ✗ Invalid choice.")
            continue
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(saved):
                deck = load_deck(saved[idx])
                if deck is None:
                    print(
                        f"  ✗ Failed to load '{saved[idx]}' — missing or invalid cards."
                    )
                    continue
                print(f"\n  ✓ Loaded: {saved[idx]}")
                for c in deck:
                    el = f"[{c.element}]" if c.element else ""
                    print(
                        f"    {c.name}{el}  ▲{c.top} ▶{c.right} ▼{c.bottom} ◀{c.left}  Lv{c.level}"
                    )
                return deck
            print(f"  ✗ Enter a number between 0 and {len(saved)}, or 'd'.")
        except ValueError:
            print(f"  ✗ Enter a number between 0 and {len(saved)}, or 'd'.")


def prompt_save_deck_ui(deck: list[Card]) -> None:
    from ..deck.shelf import deck_exists, load_deck, save_deck, validate_name

    choice = input("\n  Save this deck to shelf? (y/n/q): ").strip().lower()
    if not choice.startswith("y"):
        print("  Deck not saved.")
        return

    while True:
        name = input("  Deck name (or q to cancel): ").strip()
        if name.lower() == "q":
            print("  Deck not saved.")
            return
        error = validate_name(name)
        if error:
            print(f"  ✗ {error}")
            continue
        if deck_exists(name):
            existing = load_deck(name)
            if existing:
                existing_summary = ", ".join(c.name for c in existing[:3])
                print(
                    f"  Existing deck '{name}': {existing_summary}{' + more' if len(existing) > 3 else ''}"
                )
            overwrite = (
                input(f"  Deck '{name}' exists. Overwrite? (y/n/q): ").strip().lower()
            )
            if overwrite == "q":
                print("  Deck not saved.")
                return
            if not overwrite.startswith("y"):
                print("  Deck not saved.")
                return
        save_deck(name, deck)
        print(f"  ✓ Deck '{name}' saved!")
        break


def pause_message(message: str = "Press Enter to continue...") -> None:
    with term.cbreak(), term.hidden_cursor():
        hpad = _center_x(message) if term.does_styling else 0
        print("\n" + " " * hpad + term.dim + message)
        while True:
            k = term.inkey(timeout=None)
            if k.name == "KEY_ENTER" or k == "\n":
                play_confirm()
                break
