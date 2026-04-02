from triple_triad.models.card import Card
from triple_triad.ui.color import Color


class TestBoard:
    """Test the Board class."""

    def test_board_creation(self, empty_board):
        """Test that a board is created with 9 empty cells."""
        assert len(empty_board.cells) == 9
        assert all(cell is None for cell in empty_board.cells)

    def test_board_place(self, empty_board, sample_card):
        """Test placing a card on the board."""
        empty_board.place(0, sample_card)
        assert empty_board.cells[0] == sample_card

    def test_board_is_empty(self, empty_board):
        """Test checking if a position is empty."""
        assert empty_board.is_empty(0) is True
        assert empty_board.is_empty(4) is True
        assert empty_board.is_empty(8) is True

    def test_board_is_not_empty(self, empty_board, sample_card):
        """Test checking if a position is not empty."""
        empty_board.place(0, sample_card)
        assert empty_board.is_empty(0) is False

    def test_board_get_neighbors_center(self, empty_board):
        """Test getting neighbors for center position (4)."""
        neighbors = empty_board.get_neighbors(4)
        assert "top" in neighbors
        assert "bottom" in neighbors
        assert "left" in neighbors
        assert "right" in neighbors
        assert neighbors["top"][0] == 1
        assert neighbors["bottom"][0] == 7
        assert neighbors["left"][0] == 3
        assert neighbors["right"][0] == 5

    def test_board_get_neighbors_corner(self, empty_board):
        """Test getting neighbors for corner position (0)."""
        neighbors = empty_board.get_neighbors(0)
        assert "top" not in neighbors
        assert "bottom" in neighbors
        assert "left" not in neighbors
        assert "right" in neighbors
        assert neighbors["bottom"][0] == 3
        assert neighbors["right"][0] == 1

    def test_board_get_neighbors_edge(self, empty_board):
        """Test getting neighbors for edge position (1)."""
        neighbors = empty_board.get_neighbors(1)
        assert "top" not in neighbors
        assert "bottom" in neighbors
        assert "left" in neighbors
        assert "right" in neighbors

    def test_board_get_neighbors_with_cards(self, board_with_cards):
        """Test getting neighbors when cards are placed."""
        neighbors = board_with_cards.get_neighbors(0)
        assert neighbors["right"][1] is not None
        assert neighbors["right"][1].name == "Funguar"

    def test_board_display_empty(self, empty_board):
        """Test displaying an empty board."""
        display = empty_board.display()
        assert isinstance(display, str)
        assert len(display) > 0
        # Check that position numbers are shown
        assert "[ 1 ]" in display
        assert "[ 5 ]" in display
        assert "[ 9 ]" in display

    def test_board_display_with_cards(self, board_with_cards):
        """Test displaying a board with cards."""
        display = board_with_cards.display()
        assert isinstance(display, str)
        assert "Geezard" in display
        assert "Funguar" in display

    def test_board_full(self, full_board):
        """Test that a full board has no empty positions."""
        for i in range(9):
            assert full_board.is_empty(i) is False

    def test_board_place_multiple_cards(self, empty_board):
        """Test placing multiple cards on the board."""
        card1 = Card("Geezard")
        card1.owner = "P"
        card2 = Card("Funguar")
        card2.owner = "CPU"
        card3 = Card("Bite Bug")
        card3.owner = "P"

        empty_board.place(0, card1)
        empty_board.place(4, card2)
        empty_board.place(8, card3)

        assert empty_board.cells[0] == card1
        assert empty_board.cells[4] == card2
        assert empty_board.cells[8] == card3
        assert empty_board.is_empty(1) is True
        assert empty_board.is_empty(3) is True


class TestColor:
    """Test the Color class."""

    def test_color_player(self):
        """Test player color formatting."""
        result = Color.player("test")
        assert "test" in result
        assert Color.P_FG in result
        assert Color.RESET in result

    def test_color_cpu(self):
        """Test CPU color formatting."""
        result = Color.cpu("test")
        assert "test" in result
        assert Color.CPU_FG in result
        assert Color.RESET in result

    def test_color_border(self):
        """Test border color formatting."""
        result = Color.border("test")
        assert "test" in result
        assert Color.BORDER in result
        assert Color.RESET in result

    def test_color_empty(self):
        """Test empty position color formatting."""
        result = Color.empty("test")
        assert "test" in result
        assert Color.EMPTY_POS in result
        assert Color.RESET in result

    def test_color_card_player(self):
        """Test card color formatting for player."""
        result = Color.card("test", "P")
        assert "test" in result
        assert Color.P_FG in result

    def test_color_card_cpu(self):
        """Test card color formatting for CPU."""
        result = Color.card("test", "CPU")
        assert "test" in result
        assert Color.CPU_FG in result
