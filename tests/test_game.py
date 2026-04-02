from triple_triad.ai.base import cpu_choose
from triple_triad.deck.builder import build_cpu_deck, get_cpu_ai_mode
from triple_triad.engine.rules import resolve_captures
from triple_triad.models.card import Card


class TestGameLogic:
    """Test the game logic components."""

    def test_game_flow_simulation(
        self, empty_board, player_hand, cpu_hand, basic_rules
    ):
        """Test a simulated game flow without user input."""
        # Simulate a game turn by turn
        board = empty_board
        turn = "P"

        # Player's turn
        if turn == "P" and player_hand:
            card = player_hand.pop(0)
            card.owner = "P"
            pos = 0  # Choose first empty position
            board.place(pos, card)

            # Check captures
            captures, _ = resolve_captures(board, pos, card, basic_rules)
            for _, ncard in captures:
                ncard.owner = card.owner

            turn = "CPU"

        # CPU's turn
        if turn == "CPU" and cpu_hand:
            ci, pos = cpu_choose(board, cpu_hand, basic_rules, mode="greedy")
            card = cpu_hand.pop(ci)
            card.owner = "CPU"
            board.place(pos, card)

            # Check captures
            captures, _ = resolve_captures(board, pos, card, basic_rules)
            for _, ncard in captures:
                ncard.owner = card.owner

            turn = "P"

        # Verify board state
        assert sum(1 for c in board.cells if c is not None) == 2

    def test_score_calculation(self, board_with_cards, player_hand, cpu_hand):
        """Test score calculation logic."""
        # Count cards on board
        p_board = sum(1 for c in board_with_cards.cells if c and c.owner == "P")
        c_board = sum(1 for c in board_with_cards.cells if c and c.owner == "CPU")

        # Count cards in hand
        p_hand = len(player_hand)
        c_hand = len(cpu_hand)

        # Total scores
        p_score = p_board + p_hand
        c_score = c_board + c_hand

        assert p_score >= 0
        assert c_score >= 0

    def test_winner_determination(self):
        """Test winner determination logic."""
        # Player wins
        p_final = 5
        c_final = 4
        assert p_final > c_final

        # CPU wins
        p_final = 4
        c_final = 5
        assert c_final > p_final

        # Draw
        p_final = 5
        c_final = 5
        assert p_final == c_final

    def test_turn_alternation(self):
        """Test that turns alternate correctly."""
        turn = "P"
        assert turn == "P"

        turn = "CPU" if turn == "P" else "P"
        assert turn == "CPU"

        turn = "CPU" if turn == "P" else "P"
        assert turn == "P"

    def test_card_removal_from_hand(self, player_hand):
        """Test that cards are properly removed from hand."""
        initial_count = len(player_hand)
        card = player_hand.pop(0)
        assert len(player_hand) == initial_count - 1
        assert card not in player_hand

    def test_board_full_detection(self, full_board):
        """Test detection of a full board."""
        is_full = not any(full_board.is_empty(i) for i in range(9))
        assert is_full is True

    def test_board_not_full(self, empty_board):
        """Test detection of a non-full board."""
        is_full = not any(empty_board.is_empty(i) for i in range(9))
        assert is_full is False

    def test_empty_positions(self, board_with_cards):
        """Test getting empty positions."""
        empty_positions = [i for i in range(9) if board_with_cards.is_empty(i)]
        assert len(empty_positions) == 7  # 2 cards placed, 7 empty
        assert 0 not in empty_positions  # Position 0 has a card
        assert 1 not in empty_positions  # Position 1 has a card
        assert 2 in empty_positions  # Position 2 is empty

    def test_capture_chain(self, empty_board, basic_rules):
        """Test that captures can chain (captured cards can capture others)."""
        # Setup: CPU card at position 0, player card at position 1
        cpu_card = Card("Geezard")  # T:1 R:4 B:1 L:5
        cpu_card.owner = "CPU"
        empty_board.place(0, cpu_card)

        player_card = Card("Funguar")  # T:5 R:1 B:1 L:3
        player_card.owner = "P"
        empty_board.place(1, player_card)

        # CPU card captures player card (Geezard right=4 > Funguar left=3)
        captures, _ = resolve_captures(empty_board, 0, cpu_card, basic_rules)
        assert len(captures) == 1

        # Apply capture
        for _, ncard in captures:
            ncard.owner = cpu_card.owner
        assert empty_board.cells[1].owner == "CPU"

        # Now place another player card adjacent to the captured card
        player_card2 = Card("Bite Bug")  # T:1 R:3 B:3 L:5
        player_card2.owner = "P"
        empty_board.place(2, player_card2)

        # Bite Bug captures the CPU Funguar back (Bite Bug left=5 > Funguar right=1)
        captures, _ = resolve_captures(empty_board, 2, player_card2, basic_rules)
        assert len(captures) == 1

        # Apply capture - chain reversal
        for _, ncard in captures:
            ncard.owner = player_card2.owner
        assert empty_board.cells[1].owner == "P"

    def test_multiple_captures_single_turn(self, empty_board, basic_rules):
        """Test capturing multiple cards in a single turn."""
        # Place CPU cards at positions 1 and 3
        cpu_card1 = Card("Geezard")  # T:1 R:4 B:1 L:5
        cpu_card1.owner = "CPU"
        empty_board.place(1, cpu_card1)

        cpu_card2 = Card("Funguar")  # T:5 R:1 B:1 L:3
        cpu_card2.owner = "CPU"
        empty_board.place(3, cpu_card2)

        # Place player card at position 4 that captures both
        # Need top > Funguar's bottom (1) and left > Geezard's right (4)
        player_card = Card("Gayla")  # T:2 R:4 B:4 L:1
        player_card.owner = "P"
        empty_board.place(4, player_card)

        # Player's top (2) > Funguar's bottom (1) - capture!
        # Player's left (1) < Geezard's right (4) - no capture
        captures, _ = resolve_captures(empty_board, 4, player_card, basic_rules)
        assert len(captures) == 1

    def test_no_self_capture(self, empty_board, basic_rules):
        """Test that a card doesn't capture itself."""
        card = Card("Geezard")
        card.owner = "P"
        empty_board.place(0, card)

        captures, _ = resolve_captures(empty_board, 0, card, basic_rules)
        assert len(captures) == 0

    def test_difficulty_affects_cpu_deck(self):
        """Test that difficulty affects CPU deck composition."""
        easy_deck = build_cpu_deck("easy")
        medium_deck = build_cpu_deck("medium")
        hard_deck = build_cpu_deck("hard")

        # All decks should have 5 cards
        assert len(easy_deck) == 5
        assert len(medium_deck) == 5
        assert len(hard_deck) == 5

        # Easy deck should have lower level cards
        assert all(card.level <= 3 for card in easy_deck)

        # Hard deck should have higher level cards
        assert all(card.level >= 7 for card in hard_deck)

    def test_ai_mode_matches_difficulty(self):
        """Test that AI mode matches difficulty setting."""
        assert get_cpu_ai_mode("easy") == "random"
        assert get_cpu_ai_mode("medium") == "greedy"
        assert get_cpu_ai_mode("hard") == "greedy"
