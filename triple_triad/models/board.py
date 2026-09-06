from ..constants import BOARD_CELLS, GRID_SIZE
from ..data.cards import Element
from ..models.card import Card


class Board:
    """GRID_SIZE x GRID_SIZE grid. Positions 0..BOARD_CELLS-1 (row-major)."""

    cells: list[Card | None]
    elements: list[Element | None]

    def __init__(self, elements: list[Element | None] | None = None) -> None:
        self.cells = [None] * BOARD_CELLS
        self.elements = elements if elements is not None else [None] * BOARD_CELLS

    def place(self, pos: int, card: Card) -> None:
        self.cells[pos] = card

    def is_empty(self, pos: int) -> bool:
        return self.cells[pos] is None

    def get_neighbors(self, pos: int) -> dict[str, tuple[int, Card | None]]:
        """Return dict of direction -> (neighbor_pos, neighbor_card)."""
        row, col = divmod(pos, GRID_SIZE)
        neighbors = {}
        if row > 0:
            neighbors["top"] = (pos - GRID_SIZE, self.cells[pos - GRID_SIZE])
        if row < GRID_SIZE - 1:
            neighbors["bottom"] = (pos + GRID_SIZE, self.cells[pos + GRID_SIZE])
        if col > 0:
            neighbors["left"] = (pos - 1, self.cells[pos - 1])
        if col < GRID_SIZE - 1:
            neighbors["right"] = (pos + 1, self.cells[pos + 1])
        return neighbors
