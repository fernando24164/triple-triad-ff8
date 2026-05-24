import random
from typing import Any

from blessed import Terminal

from ..constants import DECK_SIZE
from ..data.cards import CARDS, Element
from ..models.card import Card, stat_display
from ..synth.sfx import play_cancel, play_confirm, play_cursor

ELEMENT_NAMES = [e.value for e in Element]

LEVEL_RANGES = {
    "1": ("Beginner", 1, 3),
    "2": ("Intermediate", 4, 6),
    "3": ("Advanced", 7, 10),
    "4": ("All", 1, 10),
}

PAGE_SIZE = 15


def _filter_cards(
    all_names: list[str],
    level_range: tuple[int, int] | None = None,
    element: str | None = None,
) -> list[str]:
    """Filter cards by level range and/or element."""
    result = all_names
    if level_range:
        lo, hi = level_range
        result = [n for n in result if lo <= CARDS[n].level <= hi]
    if element:
        result = [
            n
            for n in result
            if CARDS[n].element and CARDS[n].element.value == element  # type: ignore[union-attr]
        ]
    return result


def _sort_cards(
    names: list[str],
    sort_key: str = "level",
) -> list[str]:
    """Sort card names by the given key."""
    key_funcs = {
        "level": lambda n: (CARDS[n].level, n),
        "name": lambda n: n,
        "top": lambda n: (-CARDS[n].top, n),
        "right": lambda n: (-CARDS[n].right, n),
        "bottom": lambda n: (-CARDS[n].bottom, n),
        "left": lambda n: (-CARDS[n].left, n),
        "element": lambda n: (CARDS[n].element or "", n),
    }
    func = key_funcs.get(sort_key, key_funcs["level"])
    return sorted(names, key=func)


def _fill_remaining(
    chosen: list[Card],
    chosen_names: set[str],
    all_names: list[str],
) -> None:
    """Fill the deck to DECK_SIZE cards with random unchosen cards."""
    remaining = [n for n in all_names if n not in chosen_names]
    needed = DECK_SIZE - len(chosen)
    fills = random.sample(remaining, min(needed, len(remaining)))
    for name in fills:
        chosen.append(Card(name))
        chosen_names.add(name)


def _prompt_level_range() -> tuple[int, int] | None:
    print("\n  ── Level Range ──")
    for key, (label, lo, hi) in LEVEL_RANGES.items():
        print(f"  [{key}] {label} (Lv {lo}-{hi})")
    print("  [0] Cancel")
    while True:
        choice = input("  Choose range [0-4]: ").strip()
        if choice == "0":
            return None
        if choice in LEVEL_RANGES:
            _, lo, hi = LEVEL_RANGES[choice]
            return (lo, hi)
        print("  ✗ Enter 0, 1, 2, 3, or 4.")


def _prompt_element() -> str | None:
    print("\n  ── Element Filter ──")
    for i, el in enumerate(ELEMENT_NAMES, 1):
        print(f"  [{i}] {el}")
    print("  [0] Any element (no filter)")
    print("  [c] Cancel")
    while True:
        choice = input("  Choose element [0-8/c]: ").strip().lower()
        if choice == "c":
            return None
        if choice == "0":
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(ELEMENT_NAMES):
                return ELEMENT_NAMES[idx]
        except ValueError:
            pass
        print(
            f"  ✗ Enter a number between 0 and {len(ELEMENT_NAMES)}, or 'c' to cancel."
        )


def _prompt_filters(
    current_level_range: tuple[int, int] | None,
    current_element: str | None,
) -> tuple[tuple[int, int] | None, str | None]:
    print("\n  ── Current Filters ──")
    lr_label = (
        f"Level {current_level_range[0]}-{current_level_range[1]}"
        if current_level_range
        else "Any"
    )
    el_label = current_element if current_element else "Any"
    print(f"  Level range: {lr_label}")
    print(f"  Element:     {el_label}")
    print("\n  [1] Change level range")
    print("  [2] Change element filter")
    print("  [3] Clear all filters")
    print("  [0] Back to card selection")
    while True:
        choice = input("  Choice [0-3]: ").strip()
        if choice == "0":
            return current_level_range, current_element
        if choice == "1":
            new_lr = _prompt_level_range()
            return _prompt_filters(new_lr, current_element)
        if choice == "2":
            new_el = _prompt_element()
            return _prompt_filters(current_level_range, new_el)
        if choice == "3":
            return None, None
        print("  ✗ Enter 0, 1, 2, or 3.")


class _DeckPicker:
    """Interactive card picker with keyboard navigation via blessed."""

    def __init__(self) -> None:
        self.term = Terminal()
        self.all_names = sorted(CARDS.keys())
        self.level_range: tuple[int, int] | None = None
        self.element: str | None = None
        self.sort_key = "level"
        self.search_query: str | None = None
        self.chosen: list[Card] = []
        self.chosen_names: set[str] = set()
        self.page = 0
        self.cursor = 0
        self._cached_view: list[str] | None = None

    def _invalidate_cache(self) -> None:
        self._cached_view = None

    @property
    def _view_names(self) -> list[str]:
        if self._cached_view is not None:
            return self._cached_view
        names = _filter_cards(self.all_names, self.level_range, self.element)
        if self.search_query:
            q = self.search_query.lower()
            names = [n for n in names if q in n.lower()]
        self._cached_view = _sort_cards(names, self.sort_key)
        return self._cached_view

    @property
    def _total_pages(self) -> int:
        return max(
            1,
            (len(self._view_names) + self._page_capacity - 1)
            // max(1, self._page_capacity),
        )

    @property
    def _page_capacity(self) -> int:
        return max(1, self.term.height - self._fixed_rows)

    @property
    def _fixed_rows(self) -> int:
        deck_lines = 2
        if self.chosen:
            deck_lines = min(len(self.chosen), DECK_SIZE) + 4
        return 6 + deck_lines

    def _page_slice(self, view: list[str]) -> list[str]:
        start = self.page * self._page_capacity
        return view[start : start + self._page_capacity]

    def _clamp_page(self) -> None:
        self.page = max(0, min(self.page, self._total_pages - 1))

    def _clamp_cursor(self) -> None:
        count = len(self._page_slice(self._view_names))
        self.cursor = max(0, min(self.cursor, count - 1 if count else 0))

    def _draw(self) -> None:
        t = self.term
        view = self._view_names
        page_names = self._page_slice(view)
        cap = self._page_capacity
        start = self.page * cap

        lines: list[Any] = []

        def add(line: str = "") -> None:
            lines.append(line)

        def add_sep() -> None:
            add(t.cyan("  " + "─" * (t.width - 4)))

        title = f"  CARD SELECTION  —  Choose {DECK_SIZE} cards"
        info = f"Page {self.page + 1}/{self._total_pages} ({len(view)} cards)"
        pad = max(1, t.width - len(title) - len(info) - 2)
        add(t.bold_cyan(title) + t.normal + " " * pad + t.dim + info)

        filters: list[str] = []
        if self.level_range:
            filters.append(f"Level {self.level_range[0]}-{self.level_range[1]}")
        if self.element:
            filters.append(f"Element: {self.element}")
        if self.search_query:
            filters.append(f"Search: '{self.search_query}'")
        if self.sort_key != "level":
            filters.append(f"Sort: {self.sort_key}")
        add(
            t.cyan(
                f"  Filters: {' | '.join(filters)}"
                if filters
                else f"  Showing all {len(self.all_names)} cards"
            )
        )
        add_sep()

        if not self.chosen:
            add("  Deck: (empty)  ")
        else:
            add(f"  ── Your Deck ({len(self.chosen)}/{DECK_SIZE}) ──")
            total_stats = {"top": 0, "right": 0, "bottom": 0, "left": 0}
            for i, c in enumerate(self.chosen):
                el = f"[{c.element.value}]" if c.element else ""
                add(
                    f"    [{i + 1}] {c.name:<18} {el:<10} Lv{c.level}  "
                    f"▲{stat_display(c.top)} ▶{stat_display(c.right)} "
                    f"▼{stat_display(c.bottom)} ◀{stat_display(c.left)}"
                )
                total_stats["top"] += c.top
                total_stats["right"] += c.right
                total_stats["bottom"] += c.bottom
                total_stats["left"] += c.left
            add(f"    {'─' * 48}")
            add(
                f"    {'Total stats:':<28} ▲{total_stats['top']:>2} "
                f"▶{total_stats['right']:>2} ▼{total_stats['bottom']:>2} "
                f"◀{total_stats['left']:>2}"
            )
        add_sep()

        add(
            f"  {'#':>3}  {'Name':<20} {'El':<8} {'Lv':>2}  "
            f"{'▲':>2} {'▶':>2} {'▼':>2} {'◀':>2}"
        )
        add(f"  {'─' * 52}")

        for i, name in enumerate(page_names):
            stats = CARDS[name]
            el = stats.element.value if stats.element else "—"
            taken = " ✓" if name in self.chosen_names else ""
            marker = "▶" if i == self.cursor else " "
            line = (
                f"  {marker} {start + i + 1:>2}  {name:<20} {el:<8} {stats.level:>2}  "
                f"{stat_display(stats.top):>2} {stat_display(stats.right):>2} "
                f"{stat_display(stats.bottom):>2} {stat_display(stats.left):>2}{taken}"
            )
            if i == self.cursor:
                add(t.bold_black_on_cyan(line + " " * max(0, t.width - len(line) - 1)))
            else:
                add(t.white(line))

        fill = t.height - len(lines) - 1
        if fill > 0:
            add("\n" * fill)

        help_text = (
            "↑/↓ move  •  Enter select  •  n/p page  •  u undo  •  s sort  •  "
            "f level  •  / search  •  r reset  •  d done  •  q quit"
        )
        add(t.normal + t.dim + help_text + " " * max(0, t.width - len(help_text)))

        print(t.home + t.clear + "\n".join(lines), end="")

    def _show_submenu(self, title: str, items: list[str]) -> int | None:
        t = self.term
        idx = 0
        with t.cbreak(), t.hidden_cursor():
            while True:
                out: list[Any] = [t.clear]
                out.append(
                    t.move_yx(3, max(0, (t.width - len(title)) // 2))
                    + t.bold_cyan(title)
                )
                start_y = max(5, t.height // 2 - len(items) // 2)
                for i, item in enumerate(items):
                    line = f"  {item}  "
                    x = max(0, (t.width - len(line)) // 2)
                    if i == idx:
                        out.append(
                            t.move_yx(start_y + i, x) + t.bold_black_on_cyan(line)
                        )
                    else:
                        out.append(t.move_yx(start_y + i, x) + t.white(line))
                out.append(
                    t.move_yx(t.height - 2, 2)
                    + t.dim
                    + "↑/↓ move  •  Enter select  •  q back"
                )
                print("".join(out), end="")
                k = t.inkey()
                if k.name == "KEY_UP":
                    idx = (idx - 1) % len(items)
                    play_cursor()
                elif k.name == "KEY_DOWN":
                    idx = (idx + 1) % len(items)
                    play_cursor()
                elif k.name == "KEY_ENTER" or k == "\n":
                    play_confirm()
                    return idx
                elif str(k).lower() == "q":
                    play_cancel()
                    return None

    def _show_sort_menu(self) -> None:
        keys = ["level", "name", "top", "right", "bottom", "left", "element"]
        idx = self._show_submenu("Sort by", [k.capitalize() for k in keys])
        if idx is not None:
            self.sort_key = keys[idx]
            self.page = 0
            self._invalidate_cache()

    def _show_lvl_filter(self) -> None:
        lr = _prompt_level_range()
        if lr is not None:
            self.level_range = lr
            self.element = None
            self.page = 0
            self._invalidate_cache()

    def _show_search_prompt(self) -> None:
        t = self.term
        print(t.clear)
        print(
            t.move_yx(t.height // 2, 2) + t.cyan("  Search name ❯ "), end="", flush=True
        )
        with t.cbreak():
            query = ""
            while True:
                k = t.inkey()
                if k.name == "KEY_ENTER" or k == "\n":
                    break
                if str(k) == "\x7f" or k.name == "KEY_BACKSPACE":
                    query = query[:-1]
                elif k.name == "KEY_ESCAPE":
                    query = ""
                    break
                elif k.is_sequence:
                    continue
                else:
                    query += str(k)
                print(
                    t.move_yx(t.height // 2, 18) + t.white(query + " "),
                    end="",
                    flush=True,
                )
        if query:
            self.search_query = query
            self.page = 0
            self._invalidate_cache()
        else:
            self.search_query = None
            self._invalidate_cache()

    def _handle_key(self, k: Any) -> str | None:
        view = self._view_names
        cap = self._page_capacity

        if k.name == "KEY_UP":
            if self.cursor > 0:
                self.cursor -= 1
            elif self.page > 0:
                self.page -= 1
                self.cursor = cap - 1
            play_cursor()
        elif k.name == "KEY_DOWN":
            page_count = len(self._page_slice(view))
            if self.cursor < page_count - 1:
                self.cursor += 1
            elif self.page < self._total_pages - 1:
                self.page += 1
                self.cursor = 0
            play_cursor()
        elif k.name == "KEY_ENTER" or k == "\n":
            page_names = self._page_slice(view)
            if not page_names:
                return None
            name = page_names[self.cursor]
            if name in self.chosen_names:
                return None
            play_confirm()
            self.chosen.append(Card(name))
            self.chosen_names.add(name)
            if len(self.chosen) >= DECK_SIZE:
                return "break"
            page_count = len(self._page_slice(view))
            if self.cursor >= page_count - 1:
                if self.page < self._total_pages - 1:
                    self.page += 1
                    self.cursor = 0
            else:
                self.cursor += 1
        elif str(k).lower() == "n":
            if self.page < self._total_pages - 1:
                self.page += 1
                self.cursor = 0
            play_cursor()
        elif str(k).lower() == "p":
            if self.page > 0:
                self.page -= 1
                self.cursor = 0
            play_cursor()
        elif str(k).lower() == "u":
            if self.chosen:
                removed = self.chosen.pop()
                self.chosen_names.discard(removed.name)
        elif str(k).lower() == "d":
            if len(self.chosen) == 0:
                return None
            play_confirm()
            _fill_remaining(self.chosen, self.chosen_names, self.all_names)
            return "break"
        elif str(k).lower() == "r":
            self.level_range = None
            self.element = None
            self.search_query = None
            self.sort_key = "level"
            self.page = 0
            self.cursor = 0
            self._invalidate_cache()
        elif str(k).lower() == "s":
            self._show_sort_menu()
            play_confirm()
        elif str(k).lower() == "f":
            self._show_lvl_filter()
            play_confirm()
        elif str(k) == "/":
            self._show_search_prompt()
            play_confirm()
        elif str(k).lower() == "q":
            play_cancel()
            return "quit"
        return None

    def run(self) -> list[Card]:
        t = self.term
        with t.fullscreen(), t.cbreak(), t.hidden_cursor():
            while len(self.chosen) < DECK_SIZE:
                self._clamp_page()
                self._clamp_cursor()
                self._draw()
                k = t.inkey()
                if not k:
                    continue
                result = self._handle_key(k)
                if result == "break":
                    break
                if result == "quit":
                    self.chosen.clear()
                    break
        return self.chosen


def choose_deck() -> list[Card]:
    """Interactive card picker with blessed terminal UI."""
    return _DeckPicker().run()
