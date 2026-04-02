OPPOSITE = {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}


def get_attacker_value(card, direction):
    return getattr(card, direction)


def get_defender_value(card, direction):
    return getattr(card, OPPOSITE[direction])


def _evaluate_captures(board, pos, card, owner, rules):
    """Shared capture evaluation used by resolve_captures and simulate_capture.

    Returns:
        dict with keys:
            basic:  list of (pos, card) captured via normal comparison
            same:   list of (pos, card) captured via Same rule
            plus:   list of (pos, card) captured via Plus rule
            events: list of triggered rule names ("Same", "Plus")
    """
    neighbors = board.get_neighbors(pos)

    basic = []
    same_candidates = []
    plus_candidates = []

    for direction, (npos, ncard) in neighbors.items():
        if ncard is None or ncard.owner == owner:
            continue
        atk = get_attacker_value(card, direction)
        dfn = get_defender_value(ncard, direction)

        if atk > dfn:
            basic.append((npos, ncard))

        if "Same" in rules and atk == dfn:
            same_candidates.append((npos, ncard))

        if "Plus" in rules:
            plus_candidates.append((npos, ncard, atk + dfn))

    same = []
    plus = []
    events = []

    # Same rule: if 2+ neighbors have equal values
    if "Same" in rules and len(same_candidates) >= 2:
        events.append("Same")
        same = list(same_candidates)

    # Plus rule: if 2+ neighbors share the same sum
    if "Plus" in rules and len(plus_candidates) >= 2:
        sums = [x[2] for x in plus_candidates]
        for s in set(sums):
            matching = [x for x in plus_candidates if x[2] == s]
            if len(matching) >= 2:
                events.append("Plus")
                plus.extend((npos, ncard) for npos, ncard, _ in matching)

    return {"basic": basic, "same": same, "plus": plus, "events": events}


def resolve_captures(board, pos, placed_card, rules):
    """Apply basic capture logic (and Same/Plus if enabled).

    Returns:
        tuple: (captures, events) where captures is a list of (pos, card)
               tuples and events is a list of triggered rule names (e.g. "Same", "Plus").
    """
    result = _evaluate_captures(board, pos, placed_card, placed_card.owner, rules)

    captures = list(result["basic"])
    for entry in result["same"]:
        if entry not in captures:
            captures.append(entry)
    for entry in result["plus"]:
        if entry not in captures:
            captures.append(entry)

    return captures, result["events"]


def simulate_capture(board, pos, card, owner, rules):
    """
    Calculate captures for a hypothetical move without modifying state.

    This is a stateless simulation used by the AI to evaluate moves
    without the overhead of deepcopying board and card objects.

    Args:
        board: The current Board object (read-only)
        pos: Position to simulate placing at (0..BOARD_CELLS-1)
        card: Card object with top/right/bottom/left attributes
        owner: The owner of the placed card ('P' or 'CPU')
        rules: List of active rules

    Returns:
        int: Number of cards that would be captured
    """
    result = _evaluate_captures(board, pos, card, owner, rules)

    captured_positions = {npos for npos, _ in result["basic"]}
    count = len(captured_positions)

    for entry in result["same"] + result["plus"]:
        if entry[0] not in captured_positions:
            count += 1
            captured_positions.add(entry[0])

    return count
