def calculate_scores(board, player_hand, cpu_hand):
    """Return (player_score, cpu_score) based on board + hand counts."""
    p_board = sum(1 for c in board.cells if c and c.owner == "P")
    c_board = sum(1 for c in board.cells if c and c.owner == "CPU")
    return p_board + len(player_hand), c_board + len(cpu_hand)


def calculate_final_scores(board):
    """Return (player_final, cpu_final) from board ownership only."""
    p_final = sum(1 for c in board.cells if c and c.owner == "P")
    c_final = sum(1 for c in board.cells if c and c.owner == "CPU")
    return p_final, c_final
