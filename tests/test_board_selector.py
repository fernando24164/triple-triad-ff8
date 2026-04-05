"""Tests for the board selector UI module."""

import builtins
from unittest.mock import patch

from triple_triad.constants import BOARD_CELLS
from triple_triad.data.cards import Element
from triple_triad.ui.board_selector import choose_board


class TestChooseBoard:
    """Test the choose_board function."""

    def test_choose_board_none_preset(self):
        """Test happy path: selecting option 1 returns board with no elements."""
        with patch.object(builtins, "input", return_value="1"):
            board = choose_board()

        assert len(board) == BOARD_CELLS
        assert all(cell is None for cell in board)

    def test_choose_board_random_preset(self):
        """Test happy path: selecting option 2 returns board with random elements (0-2 placed)."""
        with patch.object(builtins, "input", return_value="2"):
            board = choose_board()

        assert len(board) == BOARD_CELLS
        # Count non-None elements
        non_none_count = sum(1 for cell in board if cell is not None)
        assert 0 <= non_none_count <= 2

        # Verify all non-None cells are valid Element instances
        for cell in board:
            if cell is not None:
                assert isinstance(cell, Element)
                assert cell in list(Element)

    def test_choose_board_invalid_input_defaults_to_none(self):
        """Test that invalid input defaults to option 1 (None)."""
        with patch.object(builtins, "input", return_value="invalid"):
            board = choose_board()

        assert len(board) == BOARD_CELLS
        assert all(cell is None for cell in board)

    def test_choose_board_eof_uses_default(self):
        """Test that EOFError falls back to default choice (1)."""
        with patch.object(builtins, "input", side_effect=EOFError):
            board = choose_board()

        assert len(board) == BOARD_CELLS
        assert all(cell is None for cell in board)
