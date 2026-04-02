def get_player_card_choice(hand):
    """Prompt the player to choose a card from their hand. Returns the card index."""
    while True:
        try:
            ci = int(input(f"\n  Choose card (1-{len(hand)}): ")) - 1
            if 0 <= ci < len(hand):
                return ci
            print(f"  ✗ Enter a number between 1 and {len(hand)}.")
        except ValueError:
            print("  ✗ Enter a number.")


def get_player_position_choice(board, board_cells):
    """Prompt the player to choose a position on the board. Returns the position."""
    empty = [i for i in range(board_cells) if board.is_empty(i)]
    while True:
        try:
            pos = int(input(f"  Choose position (1-{board_cells}): ")) - 1
            if pos in empty:
                return pos
            print("  ✗ Position taken or invalid.")
        except ValueError:
            print("  ✗ Enter a number.")
