from triple_triad.data.cards import Element
from triple_triad.engine.rules import (
    OPPOSITE,
    get_attacker_value,
    get_defender_value,
    resolve_captures,
)
from triple_triad.models.board import Board
from triple_triad.models.card import Card


class TestRules:
    """Test the rules and capture logic."""

    def test_opposite_dict(self):
        """Test that OPPOSITE dictionary is correct."""
        assert OPPOSITE["top"] == "bottom"
        assert OPPOSITE["bottom"] == "top"
        assert OPPOSITE["left"] == "right"
        assert OPPOSITE["right"] == "left"

    def test_get_attacker_value(self, sample_card):
        """Test getting attacker value by direction."""
        assert get_attacker_value(sample_card, "top", 4) == 1
        assert get_attacker_value(sample_card, "right", 4) == 4
        assert get_attacker_value(sample_card, "bottom", 4) == 1
        assert get_attacker_value(sample_card, "left", 4) == 5

    def test_get_defender_value(self, sample_card):
        """Test getting defender value by direction."""
        assert get_defender_value(sample_card, "top", 4) == 1  # bottom
        assert get_defender_value(sample_card, "right", 4) == 5  # left
        assert get_defender_value(sample_card, "bottom", 4) == 1  # top
        assert get_defender_value(sample_card, "left", 4) == 4  # right

    def test_basic_capture(self, empty_board, basic_rules):
        """Test basic capture logic."""
        cpu_card = Card("Geezard")  # T:1 R:4 B:1 L:5
        cpu_card.owner = "CPU"
        empty_board.place(1, cpu_card)

        player_card = Card("Funguar")  # T:5 R:1 B:1 L:3
        player_card.owner = "P"
        empty_board.place(0, player_card)

        captures, _ = resolve_captures(empty_board, 0, player_card, basic_rules)
        assert len(captures) == 0

    def test_basic_capture_success(self, empty_board, basic_rules):
        """Test successful basic capture."""
        cpu_card = Card("Geezard")  # T:1 R:4 B:1 L:5
        cpu_card.owner = "CPU"
        empty_board.place(1, cpu_card)

        player_card = Card("Red Bat")  # T:6 R:1 B:1 L:2
        player_card.owner = "P"
        empty_board.place(0, player_card)

        empty_board.cells = [None] * 9

        cpu_card = Card("Geezard")  # T:1 R:4 B:1 L:5
        cpu_card.owner = "CPU"
        empty_board.place(1, cpu_card)

        player_card = Card("Bite Bug")  # T:1 R:3 B:3 L:5
        player_card.owner = "P"
        empty_board.place(2, player_card)

        captures, _ = resolve_captures(empty_board, 2, player_card, basic_rules)
        assert len(captures) == 1
        assert captures[0][0] == 1  # position
        assert captures[0][1].name == "Geezard"

    def test_no_capture_same_owner(self, empty_board, basic_rules):
        """Test that cards with same owner don't capture."""
        card1 = Card("Geezard")
        card1.owner = "P"
        card2 = Card("Funguar")
        card2.owner = "P"

        empty_board.place(0, card1)
        empty_board.place(1, card2)

        captures, _ = resolve_captures(empty_board, 0, card1, basic_rules)
        assert len(captures) == 0

    def test_no_capture_empty_neighbor(self, empty_board, basic_rules):
        """Test that empty neighbors don't cause captures."""
        card = Card("Geezard")
        card.owner = "P"
        empty_board.place(0, card)

        captures, _ = resolve_captures(empty_board, 0, card, basic_rules)
        assert len(captures) == 0

    def test_same_rule(self, empty_board, same_rules):
        """Test Same rule activation."""
        cpu_card = Card("Geezard")  # T:1 R:4 B:1 L:5
        cpu_card.owner = "CPU"
        empty_board.place(1, cpu_card)

        cpu_card2 = Card("Funguar")  # T:5 R:1 B:1 L:3
        cpu_card2.owner = "CPU"
        empty_board.place(3, cpu_card2)

        player_card = Card("Blobra")  # T:2 R:3 B:1 L:5
        player_card.owner = "P"
        empty_board.place(0, player_card)

        empty_board.cells = [None] * 9

        cpu_card = Card("Geezard")  # T:1 R:4 B:1 L:5
        cpu_card.owner = "CPU"
        empty_board.place(1, cpu_card)

        cpu_card2 = Card("Bite Bug")  # T:1 R:3 B:3 L:5
        cpu_card2.owner = "CPU"
        empty_board.place(3, cpu_card2)

        # Place player card with matching values
        player_card = Card("Red Bat")  # T:6 R:1 B:1 L:2
        player_card.owner = "P"
        empty_board.place(0, player_card)

        captures, _ = resolve_captures(empty_board, 0, player_card, same_rules)
        assert len(captures) == 0

    def test_plus_rule(self, empty_board, plus_rules):
        """Test Plus rule activation."""
        cpu_card = Card("Geezard")  # T:1 R:4 B:1 L:5
        cpu_card.owner = "CPU"
        empty_board.place(1, cpu_card)

        cpu_card2 = Card("Funguar")  # T:5 R:1 B:1 L:3
        cpu_card2.owner = "CPU"
        empty_board.place(3, cpu_card2)

        # Player's top (2) + Geezard's bottom (1) = 3
        # Player's left (5) + Funguar's right (1) = 6
        # Not equal, so Plus won't trigger
        player_card = Card("Blobra")  # T:2 R:3 B:1 L:5
        player_card.owner = "P"
        empty_board.place(0, player_card)

        captures, _ = resolve_captures(empty_board, 0, player_card, plus_rules)
        assert len(captures) == 0

    def test_multiple_captures(self, empty_board, basic_rules):
        """Test capturing multiple cards at once."""
        cpu_card1 = Card("Geezard")  # T:1 R:4 B:1 L:5
        cpu_card1.owner = "CPU"
        empty_board.place(1, cpu_card1)

        cpu_card2 = Card("Funguar")  # T:5 R:1 B:1 L:3
        cpu_card2.owner = "CPU"
        empty_board.place(3, cpu_card2)

        player_card = Card("Red Bat")  # T:6 R:1 B:1 L:2
        player_card.owner = "P"
        empty_board.place(0, player_card)

        captures, _ = resolve_captures(empty_board, 0, player_card, basic_rules)
        assert len(captures) == 0

    def test_capture_all_directions(self, empty_board, basic_rules):
        """Test capturing in all four directions."""
        cpu_card_top = Card("Geezard")  # T:1 R:4 B:1 L:5
        cpu_card_top.owner = "CPU"
        empty_board.place(1, cpu_card_top)

        cpu_card_bottom = Card("Funguar")  # T:5 R:1 B:1 L:3
        cpu_card_bottom.owner = "CPU"
        empty_board.place(7, cpu_card_bottom)

        cpu_card_left = Card("Bite Bug")  # T:1 R:3 B:3 L:5
        cpu_card_left.owner = "CPU"
        empty_board.place(3, cpu_card_left)

        cpu_card_right = Card("Red Bat")  # T:6 R:1 B:1 L:2
        cpu_card_right.owner = "CPU"
        empty_board.place(5, cpu_card_right)

        # Place player card at center that captures all
        player_card = Card("Gayla")  # T:2 R:4 B:4 L:1
        player_card.owner = "P"
        empty_board.place(4, player_card)

        captures, _ = resolve_captures(empty_board, 4, player_card, basic_rules)
        assert len(captures) == 2

    def test_elemental_defender_penalty(self, basic_rules):
        """A mismatched element cell penalizes the defending card, not just the attacker."""
        board = Board(elements=[None, Element.FIRE] + [None] * 7)

        cpu_card = Card("Gesper")  # T:1 R:5 B:4 L:1, no element
        cpu_card.owner = "CPU"
        board.place(1, cpu_card)

        player_card = Card("Grendel")  # T:4 R:4 B:5 L:2, no element
        player_card.owner = "P"
        board.place(4, player_card)

        # Gesper doesn't match Fire, so its bottom drops to 3 -> capture.
        captures, _ = resolve_captures(board, 4, player_card, basic_rules)
        assert len(captures) == 1
        assert captures[0][1].name == "Gesper"

    def test_elemental_attacker_penalty(self, basic_rules):
        """A card placed on a mismatched element cell is weakened too."""
        board = Board(elements=[Element.WATER] + [None] * 8)

        player_card = Card("Ruby Dragon")  # T:7 R:2 B:7 L:4, Fire
        player_card.owner = "P"
        board.place(0, player_card)

        cpu_card = Card("Blood Soul")  # T:2 R:1 B:6 L:1, no element
        cpu_card.owner = "CPU"
        board.place(1, cpu_card)

        # Ruby Dragon is Fire on a Water cell, so its right drops to 1 -> tie, no capture.
        captures, _ = resolve_captures(board, 0, player_card, basic_rules)
        assert len(captures) == 0

    def test_same_wall_requires_rule_enabled(self, empty_board):
        """Same alone shouldn't count a board edge as a match."""
        cpu_card = Card("Gayla")  # T:2 R:1 B:4 L:4
        cpu_card.owner = "CPU"
        empty_board.place(4, cpu_card)

        player_card = Card("Bahamut")  # T:10 R:8 B:2 L:6
        player_card.owner = "P"
        empty_board.place(1, player_card)

        captures, events = resolve_captures(empty_board, 1, player_card, {"Same"})
        assert len(captures) == 0
        assert events == []

    def test_same_wall_captures_with_single_real_match(self, empty_board):
        """Same Wall: a board edge counts as rank A toward the 2+ match requirement."""
        cpu_card = Card("Gayla")  # T:2 R:1 B:4 L:4
        cpu_card.owner = "CPU"
        empty_board.place(4, cpu_card)

        player_card = Card("Bahamut")  # T:10 R:8 B:2 L:6
        player_card.owner = "P"
        empty_board.place(1, player_card)

        captures, events = resolve_captures(
            empty_board, 1, player_card, {"Same", "Same Wall"}
        )
        assert len(captures) == 1
        assert captures[0][1].name == "Gayla"
        assert "Same" in events

    def test_combo_chain_reaction(self, empty_board):
        """Combo: cards flipped by Same chain-capture their own neighbors."""
        center_card = Card("Belhelmel")  # T:3 R:4 B:5 L:3
        center_card.owner = "P"

        top_neighbor = Card(
            "Mesmerize"
        )  # T:5 R:3 B:3 L:4 (bottom=3 matches center top)
        top_neighbor.owner = "CPU"
        empty_board.place(1, top_neighbor)

        left_neighbor = Card(
            "Thrustaevis"
        )  # T:5 R:3 B:2 L:5 (right=3 matches center left)
        left_neighbor.owner = "CPU"
        empty_board.place(3, left_neighbor)

        chain_target_1 = Card(
            "Grat"
        )  # T:7 R:1 B:3 L:1 -> beaten by Mesmerize's left(4)
        chain_target_1.owner = "CPU"
        empty_board.place(0, chain_target_1)

        chain_target_2 = Card(
            "Geezard"
        )  # T:1 R:4 B:1 L:5 -> beaten by Thrustaevis's bottom(2)
        chain_target_2.owner = "CPU"
        empty_board.place(6, chain_target_2)

        no_rule_captures, _ = resolve_captures(empty_board, 4, center_card, set())
        assert len(no_rule_captures) == 0

        empty_board.place(4, center_card)
        captures, events = resolve_captures(empty_board, 4, center_card, {"Same"})

        captured_positions = {pos for pos, _ in captures}
        assert captured_positions == {0, 1, 3, 6}
        assert "Same" in events
        assert "Combo" in events
