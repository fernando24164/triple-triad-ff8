from ..models.board import Board
from ..models.card import Card


def calculate_scores(
    board: Board, player_hand: list[Card], cpu_hand: list[Card]
) -> tuple[int, int]:
    p_board = sum(1 for c in board.cells if c and c.owner == "P")
    c_board = sum(1 for c in board.cells if c and c.owner == "CPU")
    return p_board + len(player_hand), c_board + len(cpu_hand)


def calculate_final_scores(board: Board) -> tuple[int, int]:
    p_final = sum(1 for c in board.cells if c and c.owner == "P")
    c_final = sum(1 for c in board.cells if c and c.owner == "CPU")
    return p_final, c_final
