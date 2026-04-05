def display_hand(hand, label, show=True):
    print(f"\n  {label}'s Hand:")
    print("  " + "─" * 60)
    if show:
        for i, card in enumerate(hand, 1):
            el = f"[{card.element}]" if card.element else ""
            print(
                f"  [{i}] {card.name}{el}  "
                f"T:{card.top} R:{card.right} B:{card.bottom} L:{card.left}  "
                f"Lv:{card.level}"
            )
    else:
        for i in range(len(hand)):
            print(f"  [{i + 1}] ???")
    print("  " + "─" * 60)


def print_banner():
    print("""
 ╔══════════════════════════════════════════════════════════╗
 ║          TRIPLE TRIAD  —  Final Fantasy VIII             ║
 ║                  Text Edition  🃏                        ║
 ╚══════════════════════════════════════════════════════════╝
 """)


def print_help():
    print("""
  ╔══════════════════════════════════════════════════════════╗
  ║              TRIPLE TRIAD - HOW TO PLAY                  ║
  ╚══════════════════════════════════════════════════════════╝

  OBJECTIVE
  ─────────
  Capture more cards than your opponent on a 3×3 grid.
  Each player starts with 5 cards. The game ends when all
  9 grid spaces are filled.

  CARD ANATOMY
  ────────────
  Each card has 4 directional values (1-10) and optionally
  an element:

         ▲ Top
         │
  ◀ Left ┼ Right ▶
         │
         ▼ Bottom

  Example: Ifrit [Fire] ▲9 ▶8 ▼6 ◀5
    - Top: 9, Right: 8, Bottom: 6, Left: 5
    - Element: Fire (can affect gameplay with certain rules)

  BASIC GAMEPLAY
  ──────────────
  1. Players take turns placing one card on an empty space.
  2. When a card is placed adjacent to an opponent's card,
     compare the touching values:
       - Your card's value vs opponent's touching value
       - Higher value WINS and captures the opponent's card
  3. Captured cards change ownership (color/indicator).
  4. Game ends when all 9 spaces are filled.
  5. Player with most cards wins!

  CAPTURE EXAMPLE
  ───────────────
  Your card (Right=8) placed next to opponent's card (Left=5):
    - Your 8 > Opponent's 5 → You capture their card!

  If your card's value is LOWER or EQUAL, no capture occurs
  (unless Same/Plus rules are active).

  OPTIONAL RULES
  ──────────────
  Open:   CPU's hand is visible to you
  Same:   If 2+ adjacent cards share equal values, ALL are
          captured by the placed card
  Plus:   If 2+ adjacent cards share equal value SUMS, ALL
          are captured
  Random: Cards are dealt randomly from the full card pool

  DECK SELECTION
  ──────────────
  Before each game, choose your 5 cards:
    [1] Browse all 110 cards and pick manually
    [2] Random starter deck (low-level cards)
    [3] Random deck (any level)
    [4] Preset themed decks

  DURING YOUR TURN
  ────────────────
  - Enter a number (1-9) to place a card on the grid
  - Or enter a card number from your hand to see details
  - Strategy matters: position cards to maximize captures!

  ╔═════════════════════════════════════╗
  ║              Good luck!             ║
  ╚═════════════════════════════════════╝
  """)


def choose_rules():
    print("\n  ── Optional Rules ──")
    print("  [1] Open   — See opponent's hand")
    print("  [2] Same   — Equal values on 2+ sides = capture all")
    print("  [3] Plus   — Equal sums on 2+ sides = capture all")
    print("  [4] Random — Cards dealt randomly")
    print("  (Enter numbers separated by commas, or press Enter for none)")
    raw = input("  Your choice: ").strip()
    rules = set()
    if raw:
        for token in raw.split(","):
            token = token.strip()
            mapping = {"1": "Open", "2": "Same", "3": "Plus", "4": "Random"}
            if token in mapping:
                rules.add(mapping[token])
    return rules
