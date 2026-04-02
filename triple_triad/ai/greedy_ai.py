from ..engine.rules import simulate_capture


def greedy_choice(board, cpu_hand: list, rules, empty_positions: list):
    best_score = -1
    best_card_idx = 0
    best_pos = empty_positions[0]

    for ci, card in enumerate(cpu_hand):
        for pos in empty_positions:
            score = simulate_capture(board, pos, card, "CPU", rules)
            if score > best_score:
                best_score = score
                best_card_idx = ci
                best_pos = pos

    return best_card_idx, best_pos
