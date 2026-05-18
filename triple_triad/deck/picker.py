import random

from ..constants import DECK_SIZE
from ..data.cards import CARDS
from ..models.card import Card, stat_display

# Element names from the Element enum
ELEMENT_NAMES = ["Thunder", "Earth", "Ice", "Wind", "Poison", "Fire", "Water", "Holy"]

# Level range presets for quick filtering
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
            n for n in result if CARDS[n].element and CARDS[n].element.value == element
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


def _paginate_cards(
    all_names: list[str],
    page: int,
    page_size: int = PAGE_SIZE,
    chosen_names: set[str] | None = None,
) -> None:
    """Print one page of the card list with stats in a compact table."""
    if chosen_names is None:
        chosen_names = set()

    start = page * page_size
    end = min(start + page_size, len(all_names))
    page_names = all_names[start:end]

    if not page_names:
        print("  (no cards match your filters)")
        return

    # Header
    print(
        f"  {'#':>3}  {'Name':<20} {'El':<8} {'Lv':>2}  {'▲':>2} {'▶':>2} {'▼':>2} {'◀':>2}"
    )
    print(f"  {'─' * 52}")

    for i, name in enumerate(page_names):
        stats = CARDS[name]
        el = stats.element.value if stats.element else "—"
        taken = " ✓" if name in chosen_names else ""
        print(
            f"  {start + i + 1:>3}  {name:<20} {el:<8} {stats.level:>2}  "
            f"{stat_display(stats.top):>2} {stat_display(stats.right):>2} "
            f"{stat_display(stats.bottom):>2} {stat_display(stats.left):>2}{taken}"
        )

    total_pages = max(1, (len(all_names) + page_size - 1) // page_size)
    print(f"\n  Page {page + 1}/{total_pages}  ({len(all_names)} cards total)")


def _show_deck_preview(chosen: list[Card]) -> None:
    """Show a summary of the currently chosen deck."""
    if not chosen:
        print("  Deck: (empty)")
        return

    print(f"\n  ── Your Deck ({len(chosen)}/{DECK_SIZE}) ──")
    total_stats = {"top": 0, "right": 0, "bottom": 0, "left": 0}
    for i, c in enumerate(chosen):
        el = f"[{c.element.value}]" if c.element else ""
        print(
            f"    [{i + 1}] {c.name:<18} {el:<10} Lv{c.level}  "
            f"▲{stat_display(c.top)} ▶{stat_display(c.right)} "
            f"▼{stat_display(c.bottom)} ◀{stat_display(c.left)}"
        )
        total_stats["top"] += c.top
        total_stats["right"] += c.right
        total_stats["bottom"] += c.bottom
        total_stats["left"] += c.left

    print(f"    {'─' * 48}")
    print(
        f"    {'Total stats:':<28} ▲{total_stats['top']:>2} ▶{total_stats['right']:>2} "
        f"▼{total_stats['bottom']:>2} ◀{total_stats['left']:>2}"
    )


def _show_help() -> None:
    """Display available commands during card selection."""
    print("\n  ── Commands ──")
    print("  <number>   Pick the card with that number (0-109)")
    print("  n / p      Next / Previous page")
    print("  u          Undo last pick")
    print("  sort <key> Sort by: level, name, top, right, bottom, left, element")
    print("  filter     Apply level/element filters")
    print("  search     Search by card name")
    print("  reset      Clear all filters")
    print("  done       Finish early (auto-fill remaining)")
    print("  help       Show this help message")


def _prompt_level_range() -> tuple[int, int] | None:
    """Prompt user to select a level range. Returns (lo, hi) or None to cancel."""
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
    """Prompt user to select an element filter. Returns element name or None."""
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
            return None  # No filter
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(ELEMENT_NAMES):
                return ELEMENT_NAMES[idx]
        except ValueError:
            pass
        print(
            f"  ✗ Enter a number between 0 and {len(ELEMENT_NAMES)}, or 'c' to cancel."
        )


def _prompt_filters(current_level_range, current_element):
    """Show filter menu and return updated (level_range, element) tuple."""
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
        print(f"  ↻ Auto-filled: {name}")


def choose_deck() -> list[Card]:
    """
    Interactive card picker with hierarchical filtering:
      - Level range filter (Beginner/Intermediate/Advanced/All)
      - Element filter (Fire/Ice/Thunder/etc.)
      - Name search
      - Sorting by any stat
      - Undo support
      - Deck preview with total stats
      - Auto-fill remaining slots
    """
    all_names = sorted(CARDS.keys())

    # Filter state
    level_range: tuple[int, int] | None = None
    element: str | None = None
    sort_key = "level"
    search_query: str | None = None

    # Selection state
    chosen: list[Card] = []
    chosen_names: set[str] = set()

    # View state
    page = 0

    print("\n" + "═" * 62)
    print(f"  CARD SELECTION  —  Choose {DECK_SIZE} cards")
    print("  Type 'help' for all commands, or a card number to pick")
    print("═" * 62)

    while len(chosen) < DECK_SIZE:
        # Build the filtered/sorted view
        view_names = _filter_cards(all_names, level_range, element)
        if search_query:
            q = search_query.lower()
            view_names = [n for n in view_names if q in n.lower()]
        view_names = _sort_cards(view_names, sort_key)

        # ── Display ─────────────────────────────────────────────────────
        print("\n" + "─" * 62)

        # Show active filters
        filters = []
        if level_range:
            filters.append(f"Level {level_range[0]}-{level_range[1]}")
        if element:
            filters.append(f"Element: {element}")
        if search_query:
            filters.append(f"Search: '{search_query}'")
        if sort_key != "level":
            filters.append(f"Sort: {sort_key}")

        if filters:
            print(f"  Filters: {' | '.join(filters)}")
        else:
            print(f"  Showing all {len(all_names)} cards")

        _show_deck_preview(chosen)

        # ── Card list ───────────────────────────────────────────────────
        _paginate_cards(view_names, page, PAGE_SIZE, chosen_names)

        # ── Prompt ──────────────────────────────────────────────────────
        slot = len(chosen) + 1
        raw = input(f"\n  Pick card {slot}/{DECK_SIZE} ❯ ").strip().lower()

        if not raw:
            continue

        # ── Commands ────────────────────────────────────────────────────
        if raw == "help":
            _show_help()
            continue

        if raw == "n":
            max_page = max(0, (len(view_names) + PAGE_SIZE - 1) // PAGE_SIZE - 1)
            page = min(page + 1, max_page)
            continue

        if raw == "p":
            page = max(page - 1, 0)
            continue

        if raw == "u":
            if chosen:
                removed = chosen.pop()
                chosen_names.discard(removed.name)
                print(
                    f"  ✓ Removed [{removed.name}] from your deck ({len(chosen)}/{DECK_SIZE})"
                )
            else:
                print("  ✗ Nothing to undo.")
            continue

        if raw == "done":
            if len(chosen) == 0:
                print("  ✗ You must pick at least 1 card.")
            else:
                _fill_remaining(chosen, chosen_names, all_names)
            break

        if raw == "reset":
            level_range = None
            element = None
            search_query = None
            sort_key = "level"
            page = 0
            print("  ✓ All filters cleared.")
            continue

        if raw == "filter":
            level_range, element = _prompt_filters(level_range, element)
            page = 0
            continue

        if raw == "search":
            query = input("  Search name ❯ ").strip()
            if query:
                search_query = query
                page = 0
                results = [n for n in all_names if query.lower() in n.lower()]
                print(f"  ✓ Found {len(results)} card(s) matching '{query}'.")
            else:
                search_query = None
                print("  ✓ Search cleared.")
            continue

        if raw.startswith("sort "):
            key = raw[5:].strip()
            valid_keys = ["level", "name", "top", "right", "bottom", "left", "element"]
            if key in valid_keys:
                sort_key = key
                page = 0
                print(f"  ✓ Sorting by {key}.")
            else:
                print(f"  ✗ Valid sort keys: {', '.join(valid_keys)}")
            continue

        # ── Number pick ─────────────────────────────────────────────────
        try:
            idx = int(raw) - 1
            if not (0 <= idx < len(view_names)):
                print(f"  ✗ Enter a number between 0 and {len(view_names) - 1}.")
                continue

            name = view_names[idx]
            if name in chosen_names:
                print(f"  ✗ [{name}] is already in your deck!")
                continue

            card = Card(name)
            chosen.append(card)
            chosen_names.add(name)
            stats = CARDS[name]
            el = f"[{stats.element}]" if stats.element else ""
            print(
                f"  ✓ Added ({len(chosen)}/{DECK_SIZE}): {name}{el}  "
                f"▲{stat_display(stats.top)} ▶{stat_display(stats.right)} "
                f"▼{stat_display(stats.bottom)} ◀{stat_display(stats.left)}  Lv{stats.level}"
            )
        except ValueError:
            print("  ✗ Unknown command. Enter a card number or type 'help'.")

    return chosen
