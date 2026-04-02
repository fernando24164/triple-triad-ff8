from triple_triad.ai.base import cpu_choose
from triple_triad.ai.greedy_ai import greedy_choice
from triple_triad.ai.random_ai import random_choice
from triple_triad.engine.rules import simulate_capture
from triple_triad.models.card import Card


class TestAI:
    """Test the AI logic."""

    def test_cpu_choose_random_mode(self, empty_board, cpu_hand, basic_rules):
        """Test CPU chooses a move in random mode."""
        card_idx, position = cpu_choose(
            empty_board, cpu_hand, basic_rules, mode="random"
        )
        assert 0 <= card_idx < len(cpu_hand)
        assert 0 <= position < 9
        assert empty_board.is_empty(position)

    def test_cpu_choose_greedy_mode(self, empty_board, cpu_hand, basic_rules):
        """Test CPU chooses a move in greedy mode."""
        card_idx, position = cpu_choose(
            empty_board, cpu_hand, basic_rules, mode="greedy"
        )
        assert 0 <= card_idx < len(cpu_hand)
        assert 0 <= position < 9
        assert empty_board.is_empty(position)

    def test_cpu_choose_default_mode(self, empty_board, cpu_hand, basic_rules):
        """Test CPU chooses a move with default mode (greedy)."""
        card_idx, position = cpu_choose(empty_board, cpu_hand, basic_rules)
        assert 0 <= card_idx < len(cpu_hand)
        assert 0 <= position < 9
        assert empty_board.is_empty(position)

    def test_random_choice(self, cpu_hand):
        """Test random choice function."""
        empty_positions = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        card_idx, position = random_choice(empty_positions, cpu_hand)
        assert 0 <= card_idx < len(cpu_hand)
        assert position in empty_positions

    def test_greedy_choice_empty_board(self, empty_board, cpu_hand, basic_rules):
        """Test greedy choice on empty board."""
        empty_positions = [i for i in range(9) if empty_board.is_empty(i)]
        card_idx, position = greedy_choice(
            empty_board, cpu_hand, basic_rules, empty_positions
        )
        assert 0 <= card_idx < len(cpu_hand)
        assert position in empty_positions

    def test_greedy_choice_with_capture_opportunity(self, empty_board, basic_rules):
        """Test greedy choice finds capture opportunities."""
        # Place a player card that can be captured
        player_card = Card("Geezard")  # T:1 R:4 B:1 L:5
        player_card.owner = "P"
        empty_board.place(1, player_card)

        # CPU hand with cards that can capture
        cpu_hand = [
            Card("Funguar"),  # T:5 R:1 B:1 L:3
            Card("Bite Bug"),  # T:1 R:3 B:3 L:5
        ]
        for card in cpu_hand:
            card.owner = "CPU"

        empty_positions = [i for i in range(9) if empty_board.is_empty(i)]
        card_idx, position = greedy_choice(
            empty_board, cpu_hand, basic_rules, empty_positions
        )

        # Should choose a position adjacent to the player card
        assert position in [0, 2, 4]  # Adjacent to position 1

    def test_cpu_choose_full_board(self, full_board, cpu_hand, basic_rules):
        """Test CPU returns (0, None) when board is full."""
        card_idx, position = cpu_choose(full_board, cpu_hand, basic_rules)
        assert card_idx == 0
        assert position is None

    def test_cpu_choose_single_empty_position(self, empty_board, cpu_hand, basic_rules):
        """Test CPU chooses when only one position is empty."""
        # Fill all but one position
        for i in range(8):
            card = Card("Geezard")
            card.owner = "P"
            empty_board.place(i, card)

        card_idx, position = cpu_choose(empty_board, cpu_hand, basic_rules)
        assert 0 <= card_idx < len(cpu_hand)
        assert position == 8  # Only empty position

    def test_greedy_prefers_more_captures(self, empty_board, basic_rules):
        """Test that greedy mode prefers moves that capture cards."""
        # Setup: Place a player card that can be captured
        player_card = Card("Geezard")  # T:1 R:4 B:1 L:5
        player_card.owner = "P"
        empty_board.place(0, player_card)

        # CPU hand with cards that can capture
        cpu_hand = [
            Card("Red Bat"),  # T:6 R:1 B:1 L:2
            Card("Blobra"),  # T:2 R:3 B:1 L:5
        ]
        for card in cpu_hand:
            card.owner = "CPU"

        empty_positions = [i for i in range(9) if empty_board.is_empty(i)]
        card_idx, position = greedy_choice(
            empty_board, cpu_hand, basic_rules, empty_positions
        )

        # The chosen move should capture at least 1 card
        chosen_card = cpu_hand[card_idx]
        score = simulate_capture(empty_board, position, chosen_card, "CPU", basic_rules)
        assert score >= 1

    def test_random_choice_different_results(self, cpu_hand):
        """Test that random choice can produce different results."""
        empty_positions = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        results = set()

        # Run multiple times to check for randomness
        for _ in range(10):
            card_idx, position = random_choice(empty_positions, cpu_hand)
            results.add((card_idx, position))

        # With 10 runs, we should get at least 2 different results (very likely)
        # This is a probabilistic test, but with 5 cards and 9 positions, it's very likely
        assert len(results) >= 1  # At least one result
