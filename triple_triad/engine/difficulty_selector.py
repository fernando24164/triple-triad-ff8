from ..deck.builder import DIFFICULTY_CONFIG


def choose_difficulty() -> str:
    """Prompt the player to pick a difficulty and show what it means."""
    print("\n  ── Difficulty ──")
    options = [
        ("1", "easy"),
        ("2", "medium"),
        ("3", "hard"),
    ]
    for key, diff in options:
        cfg = DIFFICULTY_CONFIG[diff]
        print(f"  [{key}] {diff.capitalize():<8} — {cfg['description']}")

    diff_map = dict(options)
    while True:
        choice = input("\n  Choose difficulty [1/2/3]: ").strip()
        if choice in diff_map:
            selected = diff_map[choice]
            print(f"\n  ✓ Difficulty set to: {selected.upper()}")
            return selected
        print("  ✗ Please enter 1, 2, or 3.")
