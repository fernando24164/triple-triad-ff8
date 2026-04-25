from ..deck.builder import build_cpu_deck, build_random_deck
from ..engine.game_loop import run_game
from ..engine.utils import random_rules, reset_card_owners


def run_tournament(
    difficulty: str, ai_mode: str, board_elements: list
) -> tuple[int, int, int]:
    """
    Run a 3-game tournament with random rules for each game.

    Args:
        difficulty: The game difficulty level.
        ai_mode: The AI mode for the CPU.
        board_elements: The board elements configuration.

    Returns:
        A tuple of (wins, losses, draws) representing the player's record.
    """
    wins, losses, draws = 0, 0, 0
    for game_num in range(1, 4):
        rules = random_rules()
        print(f"\n{'═' * 62}")
        print(f"  TOURNAMENT — Game {game_num}/3")
        print(f"  Rules: {', '.join(sorted(rules)) if rules else 'None (Basic)'}")
        print(f"  Current Record — W:{wins} L:{losses} D:{draws}")
        print(f"{'═' * 62}")
        input("  Press Enter to start...")

        player_hand = build_random_deck()
        cpu_hand = build_cpu_deck(difficulty)
        for card in player_hand:
            card.owner = "P"
        for card in cpu_hand:
            card.owner = "CPU"

        winner = run_game(player_hand, cpu_hand, rules, ai_mode, board_elements)
        if winner == "P":
            wins += 1
        elif winner == "CPU":
            losses += 1
        else:
            draws += 1
        reset_card_owners(player_hand, cpu_hand)

    print("\n" + "═" * 62)
    print("  TOURNAMENT RESULTS")
    print("═" * 62)
    print(f"\n  Final Record — W:{wins} L:{losses} D:{draws}")
    if wins > losses:
        print("\n  🏆  TOURNAMENT CHAMPION!")
    elif losses > wins:
        print("\n  💀  TOURNAMENT LOST!")
    else:
        print("\n  🤝  TOURNAMENT TIED!")
    print()
    return wins, losses, draws
