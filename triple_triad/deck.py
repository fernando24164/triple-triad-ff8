# triple_triad/deck.py
import random

from .cards import Card, CARDS


# ── Difficulty configuration ───────────────────────────────────────────────
DIFFICULTY_CONFIG = {
    "easy": {
        "player_max_level": 9,  # Player can pick any card
        "cpu_min_level": 1,
        "cpu_max_level": 3,  # CPU stuck with weak cards
        "cpu_ai": "random",  # CPU plays randomly
        "description": "CPU uses weak cards (Lv 1-3) and plays randomly",
    },
    "medium": {
        "player_max_level": 9,
        "cpu_min_level": 4,
        "cpu_max_level": 6,  # CPU uses mid-tier cards
        "cpu_ai": "greedy",  # CPU plays greedy
        "description": "CPU uses mid-tier cards (Lv 4-6) and plays smart",
    },
    "hard": {
        "player_max_level": 9,
        "cpu_min_level": 7,
        "cpu_max_level": 9,  # CPU uses top-tier cards
        "cpu_ai": "greedy",  # CPU plays greedy
        "description": "CPU uses elite cards (Lv 7-9) and plays optimally",
    },
}


def build_starter_deck():
    """Return a list of 5 random low-level cards for the player."""
    low_cards = [name for name, data in CARDS.items() if data.level <= 3]
    chosen = random.sample(low_cards, min(5, len(low_cards)))
    return [Card(name) for name in chosen]


def build_cpu_deck(difficulty: str = "medium") -> list[Card]:
    """Build a CPU deck based on difficulty config."""
    cfg = DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["medium"])
    pool = [
        name
        for name, data in CARDS.items()
        if cfg["cpu_min_level"] <= data.level <= cfg["cpu_max_level"]
    ]
    if len(pool) < 5:
        # Fallback: widen the pool slightly to always guarantee 5 cards
        pool = sorted(CARDS.keys(), key=lambda n: CARDS[n].level)
    chosen = random.sample(pool, 5)
    return [Card(name) for name in chosen]


def get_cpu_ai_mode(difficulty: str) -> str:
    """Return the AI mode string for this difficulty."""
    return DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["medium"])["cpu_ai"]


# ── Deck Presets ───────────────────────────────────────────────────────────

DECK_PRESETS: dict[str, list[str]] = {
    "Balanced": [
        "Mesmerize",      # Lv3, no element, balanced stats
        "Cactuar",        # Lv4, no element
        "Bomb",           # Lv5, Fire
        "Iron Giant",     # Lv6, no element, strong
        "Shiva",          # Lv9, Ice, high stats
    ],
    "Fire Power": [
        "SAM08G",         # Lv4, Fire
        "Bomb",           # Lv5, Fire
        "Hexadragon",     # Lv5, Fire
        "Ruby Dragon",    # Lv6, Fire
        "Ifrit",          # Lv9, Fire
    ],
    "Ice Wall": [
        "Glacial Eye",    # Lv3, Ice
        "Snow Lion",      # Lv4, Ice
        "Shiva",          # Lv9, Ice
        "Chimera",        # Lv6, Water (cold theme)
        "Leviathan",      # Lv9, Water (cold theme)
    ],
    "Thunder Rush": [
        "Gayla",          # Lv2, Thunder
        "Cockatrice",     # Lv2, Thunder
        "Thrustaevis",    # Lv3, Wind
        "Blitz",          # Lv5, Thunder
        "Quezacotl",      # Lv9, Thunder
    ],
    "Poison Squad": [
        "Anacondaur",     # Lv3, Poison
        "Tri-Face",       # Lv4, Poison
        "Blue Dragon",    # Lv5, Poison
        "Gerogero",       # Lv7, Poison
        "Doomtrain",      # Lv9, Poison
    ],
}


def list_presets() -> list[str]:
    """Return a list of available deck preset names."""
    return list(DECK_PRESETS.keys())


def build_preset_deck(preset_name: str) -> list[Card]:
    """Build a deck from a named preset. Returns 5 cards."""
    if preset_name not in DECK_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list_presets()}")
    card_names = DECK_PRESETS[preset_name]
    return [Card(name) for name in card_names]


def build_random_deck() -> list[Card]:
    """Build a deck of 5 random cards from the full card pool."""
    all_names = list(CARDS.keys())
    chosen = random.sample(all_names, min(5, len(all_names)))
    return [Card(name) for name in chosen]


# ── Card picker helpers ────────────────────────────────────────────────────

# Element names from the Element enum
ELEMENT_NAMES = ["Thunder", "Earth", "Ice", "Wind", "Poison", "Fire", "Water", "Holy"]

# Level range presets for quick filtering
LEVEL_RANGES = {
    "1": ("Beginner", 1, 3),
    "2": ("Intermediate", 4, 6),
    "3": ("Advanced", 7, 9),
    "4": ("All", 1, 9),
}


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
        result = [n for n in result if CARDS[n].element and CARDS[n].element.value == element]
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
    page_size: int = 15,
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
    print(f"  {'#':>3}  {'Name':<20} {'El':<8} {'Lv':>2}  {'▲':>2} {'▶':>2} {'▼':>2} {'◀':>2}")
    print(f"  {'─' * 52}")

    for i, name in enumerate(page_names, start):
        stats = CARDS[name]
        el = stats.element.value if stats.element else "—"
        taken = " ✓" if name in chosen_names else ""
        print(
            f"  {i:>3}  {name:<20} {el:<8} {stats.level:>2}  "
            f"{stats.top:>2} {stats.right:>2} {stats.bottom:>2} {stats.left:>2}{taken}"
        )

    total_pages = max(1, (len(all_names) + page_size - 1) // page_size)
    print(f"\n  Page {page + 1}/{total_pages}  ({len(all_names)} cards total)")


def _show_deck_preview(chosen: list[Card]) -> None:
    """Show a summary of the currently chosen deck."""
    if not chosen:
        print("  Deck: (empty)")
        return

    print(f"\n  ── Your Deck ({len(chosen)}/5) ──")
    total_stats = {"top": 0, "right": 0, "bottom": 0, "left": 0}
    for i, c in enumerate(chosen, 1):
        el = f"[{c.element.value}]" if c.element else ""
        print(f"    [{i}] {c.name:<18} {el:<10} Lv{c.level}  ▲{c.top} ▶{c.right} ▼{c.bottom} ◀{c.left}")
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
    print("  <number>   Pick the card with that number")
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
        print(f"  ✗ Enter a number between 0 and {len(ELEMENT_NAMES)}, or 'c' to cancel.")


def _prompt_filters(current_level_range, current_element):
    """Show filter menu and return updated (level_range, element) tuple."""
    print("\n  ── Current Filters ──")
    lr_label = f"Level {current_level_range[0]}-{current_level_range[1]}" if current_level_range else "Any"
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
    PAGE_SIZE = 15

    print("\n" + "═" * 62)
    print("  CARD SELECTION  —  Choose 5 cards")
    print("  Type 'help' for all commands, or a card number to pick")
    print("═" * 62)

    while len(chosen) < 5:
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
        raw = input(f"\n  Pick card {slot}/5 ❯ ").strip().lower()

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
                print(f"  ✓ Removed [{removed.name}] from your deck ({len(chosen)}/5)")
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
                print(f"  ✗ Enter a number between 1 and {len(view_names)}.")
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
                f"  ✓ Added ({len(chosen)}/5): {name}{el}  "
                f"▲{stats.top} ▶{stats.right} ▼{stats.bottom} ◀{stats.left}  Lv{stats.level}"
            )
        except ValueError:
            print("  ✗ Unknown command. Enter a card number or type 'help'.")

    return chosen


# ── Internal helpers ───────────────────────────────────────────────────────


def _fill_remaining(
    chosen: list[Card],
    chosen_names: set[str],
    all_names: list[str],
) -> None:
    """Fill the deck to 5 cards with random unchosen cards."""
    remaining = [n for n in all_names if n not in chosen_names]
    needed = 5 - len(chosen)
    fills = random.sample(remaining, min(needed, len(remaining)))
    for name in fills:
        chosen.append(Card(name))
        chosen_names.add(name)
        print(f"  ↻ Auto-filled: {name}")