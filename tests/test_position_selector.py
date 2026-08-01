from triple_triad.ui.position_selector import next_empty_in_direction


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

    def test_skip_occupied_cell(self, empty_board, sample_card):
        empty_board.place(1, sample_card)
        assert next_empty_in_direction(empty_board, 4, "KEY_UP") == 7

    def test_skip_occupied_then_wrap(self, empty_board, sample_card):
        for pos in (1, 4):
            empty_board.place(pos, sample_card)
        assert next_empty_in_direction(empty_board, 4, "KEY_UP") == 7

    def test_no_empty_in_column(self, empty_board, sample_card):
        for pos in (1, 4, 7):
            empty_board.place(pos, sample_card)
        assert next_empty_in_direction(empty_board, 1, "KEY_UP") is None

    def test_no_empty_in_row(self, empty_board, sample_card):
        for pos in (3, 4, 5):
            empty_board.place(pos, sample_card)
        assert next_empty_in_direction(empty_board, 4, "KEY_LEFT") is None

    def test_never_returns_current_cell(self, empty_board):
        for key in ("KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"):
            assert next_empty_in_direction(empty_board, 4, key) != 4

    def test_unknown_key(self, empty_board):
        assert next_empty_in_direction(empty_board, 4, "KEY_HOME") is None
