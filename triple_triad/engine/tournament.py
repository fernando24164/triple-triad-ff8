from __future__ import annotations

from typing import TYPE_CHECKING

from ..data.cards import Element
from ..deck.builder import build_cpu_deck, build_random_deck
from ..engine.game_loop import run_game
from ..engine.utils import random_rules, reset_card_owners
from ..ui.tournament_display import (
    build_bracket,
    show_bracket_reveal,
    show_champion_finale,
    show_round_intro,
    show_round_result,
)

if TYPE_CHECKING:
    from ..synth.player import ChiptunePlayer


def run_tournament(
    difficulty: str,
    ai_mode: str,
    board_elements: list[Element | None],
    ai_randomness: float = 0.0,
    music_player: ChiptunePlayer | None = None,
) -> tuple[int, int, int] | None:
    """
    Run a 3-game tournament with random rules for each game.

    Args:
        difficulty: The game difficulty level.
        ai_mode: The AI mode for the CPU.
        board_elements: The board elements configuration.
        ai_randomness: The greedy-AI randomness factor for the CPU.
        music_player: Shared menu music player, ducked to the gameplay
            theme for each match and restored afterward.

    Returns:
        A tuple of (wins, losses, draws) representing the player's record,
        or None when the player quit a match early.
    """
    wins, losses, draws = 0, 0, 0
    matches = build_bracket()
    show_bracket_reveal(matches)

    for game_num in range(1, 4):
        round_index = game_num - 1
        rules = random_rules()
        show_round_intro(matches, round_index)
        print(f"  Rules: {', '.join(sorted(rules)) if rules else 'None (Basic)'}")
        print(f"  Current Record — W:{wins} L:{losses} D:{draws}")
        input("  Press Enter to start...")

        player_hand = build_random_deck()
        cpu_hand = build_cpu_deck(difficulty)
        for card in player_hand:
            card.owner = "P"
        for card in cpu_hand:
            card.owner = "CPU"

        winner = run_game(
            player_hand,
            cpu_hand,
            rules,
            ai_mode,
            board_elements,
            ai_randomness,
            music_player=music_player,
        )
        if winner == "quit":
            print("\n  Tournament cancelled.")
            return None
        if winner == "P":
            wins += 1
            result = "W"
        elif winner == "CPU":
            losses += 1
            result = "L"
        else:
            draws += 1
            result = "D"
        show_round_result(matches, round_index, result)
        reset_card_owners(player_hand, cpu_hand)

    show_champion_finale(matches)
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
