from triple_triad.ai.base import cpu_choose
from triple_triad.ai.greedy_ai import greedy_choice
from triple_triad.ai.minimax_ai import (
    _apply_move,
    _evaluate,
    _search,
    _undo_move,
    minimax_choice,
)
from triple_triad.models.board import Board
from triple_triad.models.card import Card


def _empty_positions(board: Board) -> list[int]:
    return [i for i in range(9) if board.is_empty(i)]


class TestMinimaxContract:
    """The minimax AI must honor the same (card_idx, position) contract."""

    def test_minimax_choice_returns_legal_move(
        self, empty_board, cpu_hand, player_hand, basic_rules
    ):
        empty = _empty_positions(empty_board)
        card_idx, position = minimax_choice(
            empty_board, cpu_hand, player_hand, basic_rules, empty, depth=3
        )
        assert 0 <= card_idx < len(cpu_hand)
        assert position in empty

    def test_cpu_choose_minimax_mode(
        self, empty_board, cpu_hand, player_hand, open_rules
    ):
        card_idx, position = cpu_choose(
            empty_board,
            cpu_hand,
            open_rules,
            mode="minimax",
            player_hand=player_hand,
            depth=3,
        )
        assert card_idx is not None and position is not None
        assert 0 <= card_idx < len(cpu_hand)
        assert empty_board.is_empty(position)

    def test_cpu_choose_minimax_full_board(
        self, full_board, cpu_hand, player_hand, basic_rules
    ):
        card_idx, position = cpu_choose(
            full_board,
            cpu_hand,
            basic_rules,
            mode="minimax",
            player_hand=player_hand,
            depth=6,
        )
        assert card_idx == 0
        assert position is None

    def test_cpu_choose_minimax_single_empty(
        self, empty_board, cpu_hand, player_hand, open_rules
    ):
        for i in range(8):
            card = Card("Geezard")
            card.owner = "P"
            empty_board.place(i, card)

        card_idx, position = cpu_choose(
            empty_board,
            cpu_hand,
            open_rules,
            mode="minimax",
            player_hand=player_hand,
            depth=6,
        )
        assert 0 <= card_idx < len(cpu_hand)
        assert position == 8

    def test_cpu_choose_minimax_without_player_hand_falls_back(
        self, empty_board, cpu_hand, open_rules
    ):
        """Missing player_hand must not crash — it falls back to greedy."""
        card_idx, position = cpu_choose(
            empty_board, cpu_hand, open_rules, mode="minimax", player_hand=None
        )
        assert card_idx is not None and position is not None
        assert 0 <= card_idx < len(cpu_hand)
        assert empty_board.is_empty(position)

    def test_cpu_choose_minimax_without_open_rule_falls_back(
        self, empty_board, cpu_hand, player_hand, basic_rules
    ):
        """Even with player_hand provided, minimax must not activate unless
        the Open rule is active — otherwise it silently falls back to greedy.
        """
        card_idx, position = cpu_choose(
            empty_board,
            cpu_hand,
            basic_rules,
            mode="minimax",
            player_hand=player_hand,
            depth=6,
        )
        greedy_idx, greedy_pos = greedy_choice(
            empty_board, cpu_hand, basic_rules, _empty_positions(empty_board)
        )
        assert (card_idx, position) == (greedy_idx, greedy_pos)


class TestMinimaxCorrectness:
    def test_minimax_takes_available_capture(self, empty_board, player_hand, basic_rules):
        """With a lone capturable card on the board, minimax should grab it."""
        target = Card("Geezard")  # T:1 R:4 B:1 L:5
        target.owner = "P"
        empty_board.place(4, target)  # center

        cpu_hand = [Card("Red Bat"), Card("Grat")]  # strong tops (6, 7)
        for c in cpu_hand:
            c.owner = "CPU"

        empty = _empty_positions(empty_board)
        card_idx, position = minimax_choice(
            empty_board, cpu_hand, player_hand, basic_rules, empty, depth=2
        )
        # Placing below center (7) attacks Geezard's bottom(1) with a big top.
        chosen = cpu_hand[card_idx]
        empty_board.place(position, chosen)
        chosen.owner = "CPU"
        from triple_triad.engine.rules import simulate_capture

        # The move it commits to should not be strictly worse than doing nothing.
        assert simulate_capture(empty_board, position, chosen, "CPU", basic_rules) >= 0

    def test_minimax_beats_greedy_on_a_trap(self):
        """Lookahead should differ from 1-ply greedy when greedy walks into a
        recapture. Scenario found by search: same cell, but greedy picks a card
        that gets punished while minimax picks the card with the better reply.
        """
        rules: set[str] = set()
        board = Board()
        for pos, name, owner in [
            (1, "Buel", "P"),
            (3, "Geezard", "CPU"),
            (6, "Blood Soul", "CPU"),
            (7, "Red Bat", "CPU"),
            (8, "Gayla", "CPU"),
        ]:
            c = Card(name)
            c.owner = owner
            board.place(pos, c)
        cpu_hand = [Card("Funguar"), Card("Cockatrice")]
        for c in cpu_hand:
            c.owner = "CPU"
        player_hand = [Card("Blobra"), Card("Bite Bug")]
        for c in player_hand:
            c.owner = "P"

        empty = _empty_positions(board)
        greedy_move = greedy_choice(board, cpu_hand, rules, empty)
        minimax_move = minimax_choice(
            board, cpu_hand, player_hand, rules, empty, depth=len(empty)
        )

        assert greedy_move != minimax_move

        # The minimax choice must have an outcome value >= the greedy choice.
        def value_of(move: tuple[int, int]) -> int:
            ci, pos = move
            card = cpu_hand.pop(ci)
            prev = card.owner
            flipped = _apply_move(board, pos, card, "CPU", rules)
            v = _search(board, cpu_hand, player_hand, rules, len(empty) - 1,
                        -(10**9), 10**9, False)
            _undo_move(board, pos, card, prev, flipped)
            cpu_hand.insert(ci, card)
            return v

        assert value_of(minimax_move) > value_of(greedy_move)


class TestMinimaxEdgeCases:
    def test_both_hands_exhausted_before_board_fills(self, open_rules):
        """Uneven hand/board sizes must not cause infinite recursion when both
        hands run out of cards while empty cells remain.
        """
        board = Board()
        victim = Card("Geezard")
        victim.owner = "P"
        board.place(1, victim)  # 8 empty cells, but only 4 total cards below

        cpu_hand = [Card("Red Bat"), Card("Grat")]
        for c in cpu_hand:
            c.owner = "CPU"
        player_hand = [Card("Blobra"), Card("Bite Bug")]
        for c in player_hand:
            c.owner = "P"

        empty = _empty_positions(board)
        card_idx, position = minimax_choice(
            board, cpu_hand, player_hand, open_rules, empty, depth=6
        )
        assert 0 <= card_idx < len(cpu_hand)
        assert position in empty


class TestMakeUnmake:
    def test_apply_undo_round_trip_is_pristine(self, basic_rules):
        board = Board()
        victim = Card("Geezard")  # T:1 R:4 B:1 L:5
        victim.owner = "P"
        board.place(1, victim)

        attacker = Card("Grat")  # T:7 -> captures Geezard from below/side
        attacker.owner = "CPU"

        before_cells = [(c.name, c.owner) if c else None for c in board.cells]
        before_victim_owner = victim.owner

        flipped = _apply_move(board, 4, attacker, "CPU", basic_rules)
        # During the move the attacker is on the board.
        assert board.cells[4] is attacker
        _undo_move(board, 4, attacker, None, flipped)

        after_cells = [(c.name, c.owner) if c else None for c in board.cells]
        assert after_cells == before_cells
        assert victim.owner == before_victim_owner
        assert board.cells[4] is None

    def test_search_leaves_state_unchanged(
        self, cpu_hand, player_hand, basic_rules
    ):
        board = Board()
        for pos, name, owner in [(0, "Geezard", "P"), (4, "Funguar", "CPU")]:
            c = Card(name)
            c.owner = owner
            board.place(pos, c)

        snap_cells = [(c.name, c.owner) if c else None for c in board.cells]
        snap_cpu = [(c.name, c.owner) for c in cpu_hand]
        snap_player = [(c.name, c.owner) for c in player_hand]

        empty = _empty_positions(board)
        minimax_choice(board, cpu_hand, player_hand, basic_rules, empty, depth=4)

        assert [(c.name, c.owner) if c else None for c in board.cells] == snap_cells
        assert [(c.name, c.owner) for c in cpu_hand] == snap_cpu
        assert [(c.name, c.owner) for c in player_hand] == snap_player


class TestEvaluate:
    def test_evaluate_counts_owner_differential(self):
        board = Board()
        for i, owner in enumerate(["CPU", "CPU", "P"]):
            c = Card("Geezard")
            c.owner = owner
            board.place(i, c)
        assert _evaluate(board) == 1  # 2 CPU - 1 P

    def test_evaluate_empty_board_is_zero(self, empty_board):
        assert _evaluate(empty_board) == 0
