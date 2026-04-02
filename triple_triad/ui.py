# UI functions for display


def display_hand(hand, label, show=True):
    print(f"\n  {label}'s Hand:")
    print("  " + "─" * 60)
    if show:
        for i, card in enumerate(hand, 1):
            el = f"[{card.element}]" if card.element else ""
            print(f"  [{i}] {card.name}{el}  "
                  f"T:{card.top} R:{card.right} B:{card.bottom} L:{card.left}  "
                  f"Lv:{card.level}")
    else:
        for i in range(len(hand)):
            print(f"  [{i+1}] ???")
    print("  " + "─" * 60)


def print_banner():
    print("""
 ╔══════════════════════════════════════════════════════════╗
 ║          TRIPLE TRIAD  —  Final Fantasy VIII             ║
 ║                  Text Edition  🃏                        ║
 ╚══════════════════════════════════════════════════════════╝
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
        for token in raw.split(','):
            token = token.strip()
            mapping = {'1': 'Open', '2': 'Same', '3': 'Plus', '4': 'Random'}
            if token in mapping:
                rules.add(mapping[token])
    return rules
