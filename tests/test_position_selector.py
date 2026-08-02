from unittest.mock import MagicMock

import pytest

from triple_triad.ui.position_selector import (
    QuitGameError,
    next_empty_in_direction,
    select_position,
)


class _Key:
    def __init__(self, name=None, value=""):
        self.name = name
        self._value = value

    def __str__(self):
        return self._value

    def __eq__(self, other):
        return self._value == other


class TestNextEmptyInDirection:
    """Test cursor movement over the board grid."""

    def test_move_up_from_center(self, empty_board):
        assert next_empty_in_direction(empty_board, 4, "KEY_UP") == 1

    def test_move_down_from_center(self, empty_board):
        assert next_empty_in_direction(empty_board, 4, "KEY_DOWN") == 7

    def test_move_left_from_center(self, empty_board):
        assert next_empty_in_direction(empty_board, 4, "KEY_LEFT") == 3

    def test_move_right_from_center(self, empty_board):
        assert next_empty_in_direction(empty_board, 4, "KEY_RIGHT") == 5

    def test_wrap_up_from_top_row(self, empty_board):
        assert next_empty_in_direction(empty_board, 1, "KEY_UP") == 7

    def test_wrap_down_from_bottom_row(self, empty_board):
        assert next_empty_in_direction(empty_board, 7, "KEY_DOWN") == 1

    def test_wrap_left_from_first_col(self, empty_board):
        assert next_empty_in_direction(empty_board, 3, "KEY_LEFT") == 5

    def test_wrap_right_from_last_col(self, empty_board):
        assert next_empty_in_direction(empty_board, 5, "KEY_RIGHT") == 3

    def test_skip_occupied_snaps_in_line(self, empty_board, sample_card):
        # Top-middle (0,1) taken: UP from center snaps to the nearest empty
        # in the top row — both corners are 1 step away, ties go to the
        # lower cell index (top-left).
        empty_board.place(1, sample_card)
        assert next_empty_in_direction(empty_board, 4, "KEY_UP") == 0

    def test_full_column_snaps_in_line(self, empty_board, sample_card):
        for pos in (1, 4, 7):
            empty_board.place(pos, sample_card)
        # Column 1 fully blocked: UP wraps to the bottom row, both ends are
        # 1 step away from (0,1) — ties go to the lower cell index.
        assert next_empty_in_direction(empty_board, 1, "KEY_UP") == 6

    def test_full_row_snaps_in_line(self, empty_board, sample_card):
        for pos in (3, 4, 5):
            empty_board.place(pos, sample_card)
        # Row 1 fully blocked: LEFT wraps to column 0, both ends are 1 row
        # away from (1,1) — ties go to the lower cell index.
        assert next_empty_in_direction(empty_board, 4, "KEY_LEFT") == 0

    def test_never_returns_current_cell(self, empty_board):
        for key in ("KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"):
            assert next_empty_in_direction(empty_board, 4, key) != 4

    def test_unknown_key(self, empty_board):
        assert next_empty_in_direction(empty_board, 4, "KEY_HOME") is None

    def test_opposite_corners_reachable_down(self, empty_board, sample_card):
        for pos in range(1, 8):
            empty_board.place(pos, sample_card)
        assert next_empty_in_direction(empty_board, 0, "KEY_DOWN") == 8

    def test_opposite_corners_reachable_up(self, empty_board, sample_card):
        for pos in range(1, 8):
            empty_board.place(pos, sample_card)
        assert next_empty_in_direction(empty_board, 8, "KEY_UP") == 0

    def test_opposite_corners_reachable_left(self, empty_board, sample_card):
        for pos in range(1, 8):
            empty_board.place(pos, sample_card)
        assert next_empty_in_direction(empty_board, 8, "KEY_LEFT") == 0

    def test_diagonal_reachable_when_line_blocked(self, empty_board, sample_card):
        for pos in range(9):
            if pos not in (0, 4):
                empty_board.place(pos, sample_card)
        assert next_empty_in_direction(empty_board, 0, "KEY_DOWN") == 4

    def test_straight_line_preferred_when_free(self, empty_board, sample_card):
        # Free cells: (0,0), (0,1), (2,2). RIGHT from (0,0) must take the
        # straight-line (0,1) instead of fanning out to (2,2).
        for pos in range(9):
            if pos not in (0, 1, 8):
                empty_board.place(pos, sample_card)
        assert next_empty_in_direction(empty_board, 0, "KEY_RIGHT") == 1


class TestSelectPosition:
    def test_returns_chosen_position(self, empty_board):
        term = MagicMock()
        term.inkey.side_effect = [_Key("KEY_DOWN"), _Key("KEY_ENTER")]
        pos = select_position(empty_board, term, True, lambda h: None)
        assert pos == 3

    def test_cancel_returns_none(self, empty_board):
        term = MagicMock()
        term.inkey.side_effect = [_Key("KEY_ESCAPE")]
        assert select_position(empty_board, term, True, lambda h: None) is None

    def test_quit_raises(self, empty_board):
        term = MagicMock()
        term.inkey.side_effect = [_Key(value="q")]
        with pytest.raises(QuitGameError):
            select_position(empty_board, term, True, lambda h: None)

    def test_non_screen_returns_none(self, empty_board):
        assert select_position(empty_board, None, False, lambda h: None) is None

    def test_full_board_returns_none(self, full_board):
        term = MagicMock()
        assert select_position(full_board, term, True, lambda h: None) is None
