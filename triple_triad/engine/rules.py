from collections.abc import Collection
from typing import Any, cast

from ..data.cards import Element
from ..models.board import Board
from ..models.card import Card

OPPOSITE = {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}
DIRECTIONS = ("top", "bottom", "left", "right")
WALL_RANK = 10  # Same Wall: board edges count as rank A for the Same rule


def _elemental_bonus(
    card: Card, pos: int, board_elements: list[Element | None] | None
) -> int:
    """+1 if the card's element matches its cell, -1 if the cell has an
    element and it doesn't match (including elementless cards), else 0."""
    if not board_elements or pos >= len(board_elements):
        return 0
    cell_element = board_elements[pos]
    if cell_element is None:
        return 0
    return 1 if card.element == cell_element else -1


def get_attacker_value(
    card: Card,
    direction: str,
    pos: int,
    board_elements: list[Element | None] | None = None,
) -> int:
    base_value: int = cast(int, getattr(card, direction))
    return base_value + _elemental_bonus(card, pos, board_elements)


def get_defender_value(
    card: Card,
    direction: str,
    pos: int,
    board_elements: list[Element | None] | None = None,
) -> int:
    base_value: int = cast(int, getattr(card, OPPOSITE[direction]))
    return base_value + _elemental_bonus(card, pos, board_elements)


def _evaluate_captures(
    board: Board, pos: int, card: Card, owner: str | None, rules: Collection[str]
) -> dict[str, Any]:
    """Shared capture evaluation used by resolve_captures and simulate_capture.

    Returns:
        dict with keys:
            basic:  list of (pos, card) captured via normal comparison
            same:   list of (pos, card) captured via Same rule
            plus:   list of (pos, card) captured via Plus rule
            events: list of triggered rule names ("Same", "Plus")
    """
    neighbors = board.get_neighbors(pos)
    board_elements = getattr(board, "elements", None)

    basic: list[tuple[int, Card]] = []
    same_candidates: list[tuple[int, Card]] = []
    plus_candidates: list[tuple[int, Card, int]] = []

    for direction, (npos, ncard) in neighbors.items():
        if ncard is None or ncard.owner == owner:
            continue
        atk = get_attacker_value(card, direction, pos, board_elements)
        dfn = get_defender_value(ncard, direction, npos, board_elements)

        if atk > dfn:
            basic.append((npos, ncard))

        if "Same" in rules and atk == dfn:
            same_candidates.append((npos, ncard))

        if "Plus" in rules:
            plus_candidates.append((npos, ncard, atk + dfn))

    # Same Wall: board edges count as rank A (10) toward the Same rule's
    # 2+ match requirement, but a wall has no card to capture.
    wall_matches = 0
    if "Same" in rules and "Same Wall" in rules:
        missing_directions = set(DIRECTIONS) - set(neighbors.keys())
        for direction in missing_directions:
            if get_attacker_value(card, direction, pos, board_elements) == WALL_RANK:
                wall_matches += 1

    same: list[tuple[int, Card]] = []
    plus: list[tuple[int, Card]] = []
    events: list[str] = []

    # Same rule: if 2+ neighbors (plus matching walls) have equal values
    if "Same" in rules and same_candidates and len(same_candidates) + wall_matches >= 2:
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


def _cascade_combo(
    board: Board,
    seeds: list[tuple[int, Card]],
    attacker_owner: str | None,
    board_elements: list[Element | None] | None,
) -> list[tuple[int, Card]]:
    """Combo rule: cards flipped by Same/Plus (or Same Wall) chain-react
    against their own neighbors using the basic (higher-value-wins) rule
    only — Same/Plus are not re-evaluated during the chain."""
    captured_positions = {p for p, _ in seeds}
    queue = list(seeds)
    extra: list[tuple[int, Card]] = []

    while queue:
        cpos, ccard = queue.pop(0)
        for direction, (npos, ncard) in board.get_neighbors(cpos).items():
            if ncard is None or npos in captured_positions:
                continue
            if ncard.owner == attacker_owner:
                continue
            atk = get_attacker_value(ccard, direction, cpos, board_elements)
            dfn = get_defender_value(ncard, direction, npos, board_elements)
            if atk > dfn:
                captured_positions.add(npos)
                entry = (npos, ncard)
                extra.append(entry)
                queue.append(entry)

    return extra


def resolve_captures(
    board: Board, pos: int, placed_card: Card, rules: Collection[str]
) -> tuple[list[tuple[int, Card]], list[str]]:
    """Apply basic capture logic (and Same/Plus/Same Wall/Combo if enabled).

    Returns:
        tuple: (captures, events) where captures is a list of (pos, card)
               tuples and events is a list of triggered rule names (e.g. "Same", "Plus").
    """
    result = _evaluate_captures(board, pos, placed_card, placed_card.owner, rules)

    captures: list[tuple[int, Card]] = list(result["basic"])
    for entry in result["same"]:
        if entry not in captures:
            captures.append(entry)
    for entry in result["plus"]:
        if entry not in captures:
            captures.append(entry)

    events: list[str] = list(result["events"])

    # Combo: automatic side effect of Same/Plus — every card flipped this
    # turn can chain-capture further neighbors via the basic rule.
    if events:
        board_elements = getattr(board, "elements", None)
        extra = _cascade_combo(board, captures, placed_card.owner, board_elements)
        new_extra = [entry for entry in extra if entry not in captures]
        if new_extra:
            captures.extend(new_extra)
            events.append("Combo")

    return captures, events


def simulate_capture(
    board: Board, pos: int, card: Card, owner: str | None, rules: Collection[str]
) -> int:
    """
    Calculate captures for a hypothetical move without modifying state.

    This is a stateless simulation used by the AI to evaluate moves
    without the overhead of deepcopying board and card objects.

    Args:
        board: The current Board object (read-only)
        pos: Position to simulate placing at (0..BOARD_CELLS-1)
        card: Card object with top/right/bottom/left attributes
        owner: The owner of the placed card ('P', 'CPU', or None for simulation)
        rules: List of active rules

    Returns:
        int: Number of cards that would be captured
    """
    result = _evaluate_captures(board, pos, card, owner, rules)

    seeds: list[tuple[int, Card]] = list(result["basic"])
    captured_positions: set[int] = {npos for npos, _ in seeds}

    for entry in result["same"] + result["plus"]:
        if entry[0] not in captured_positions:
            captured_positions.add(entry[0])
            seeds.append(entry)

    if result["events"]:
        board_elements = getattr(board, "elements", None)
        extra = _cascade_combo(board, seeds, owner, board_elements)
        captured_positions.update(npos for npos, _ in extra)

    return len(captured_positions)
