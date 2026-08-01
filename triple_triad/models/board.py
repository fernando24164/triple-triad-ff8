from ..constants import BOARD_CELLS, GRID_SIZE
from ..data.cards import Element
from ..models.card import Card, stat_display
from ..ui.color import Color


class Board:
    """GRID_SIZE x GRID_SIZE grid. Positions 0..BOARD_CELLS-1 (row-major)."""

    CELL_W = 18  # inner width of each cell (visible characters only)
    cells: list[Card | None]
    elements: list[Element | None]

    def __init__(self, elements: list[Element | None] | None = None):
        self.cells = [None] * BOARD_CELLS  # Card or None
        self.elements = elements if elements is not None else [None] * BOARD_CELLS

    @classmethod
    def total_width(cls) -> int:
        """Visible width (chars) of one line from ``display()``."""
        return GRID_SIZE * (cls.CELL_W + 1) + 1

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

    # ── Per-cell row renderers ─────────────────────────────────────────────
    # Each method returns a string of exactly CELL_W *visible* characters.
    # ANSI codes are injected AFTER the plain-text layout is built, so
    # padding/alignment is always calculated on raw strings first.

    @staticmethod
    def _render_row1(card: Card | None) -> str:
        """Owner symbol + card name, left-aligned."""
        w = Board.CELL_W
        if card is None:
            return " " * w
        sym = "■" if card.owner == "P" else "□"
        label = f"{sym}{card.name}"
        label = label[: w - 1]  # truncate to visible width
        plain = f" {label:<{w - 1}}"  # exactly CELL_W visible chars
        return Color.card(plain, card.owner)

    @staticmethod
    def _render_row2(card: Card | None) -> str:
        """Top value centered with up-arrow."""
        w = Board.CELL_W
        if card is None:
            return " " * w
        plain = f"{'▲ ' + stat_display(card.top):^{w}}"
        return Color.card(plain, card.owner)

    @staticmethod
    def _render_row3(card: Card | None) -> str:
        """Left value — element — right value, all on one line."""
        w = Board.CELL_W
        if card is None:
            return " " * w

        el = card.element[:3] if card.element else "   "

        left_str = f"◀ {stat_display(card.left)}"
        right_str = f"{stat_display(card.right)} ▶"

        # 1. Build a plain CELL_W-char canvas filled with spaces
        chars = [" "] * w

        # 2. Write the element centred  (occupies positions  1 .. w-2)
        inner = w - 2  # 16 visible chars
        el_padded = f"{el:^{inner}}"  # e.g. "      Ice      "
        for i, ch in enumerate(el_padded):
            chars[1 + i] = ch

        # 3. Overlay left value at position 1 (overwrites element if needed)
        for i, ch in enumerate(left_str):
            chars[1 + i] = ch

        # 4. Overlay right value ending at position w-1
        start_r = w - 1 - len(right_str)
        for i, ch in enumerate(right_str):
            chars[start_r + i] = ch

        plain = "".join(chars)
        return Color.card(plain, card.owner)

    @staticmethod
    def _render_row4(card: Card | None) -> str:
        """Bottom value centered with down-arrow."""
        w = Board.CELL_W
        if card is None:
            return " " * w
        plain = f"{'▼ ' + stat_display(card.bottom):^{w}}"
        return Color.card(plain, card.owner)

    @staticmethod
    def _render_empty(pos: int, element: Element | None = None) -> str:
        """Empty cell: show position number centred on row 3."""
        w = Board.CELL_W
        if element:
            el_abbr = element.value[:3]
            label = f"[{pos + 1}] {el_abbr}"
        else:
            label = f"[ {pos + 1} ]"
        plain = f"{label:^{w}}"
        return Color.empty(plain)

    # ── Border helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _colored_border(text: str) -> str:
        return Color.border(text)

    @classmethod
    def _hline(
        cls,
        left: str,
        mid: str,
        right: str,
        fill: str,
        highlight_col: int | None = None,
    ) -> str:
        segment = fill * cls.CELL_W
        line = left + (mid.join([segment] * GRID_SIZE)) + right
        if highlight_col is None or not 0 <= highlight_col < GRID_SIZE:
            return cls._colored_border(line)
        # Span covering the segment of the highlighted column plus the
        # junction chars on both of its ends.
        span_start = highlight_col * (cls.CELL_W + 1)
        span_end = span_start + cls.CELL_W + 1
        return (
            cls._colored_border(line[:span_start])
            + Color.highlight(line[span_start:span_end])
            + cls._colored_border(line[span_end:])
        )

    # ── Main renderer ──────────────────────────────────────────────────────

    def display(self, highlight: int | None = None) -> str:
        """Render the board. When ``highlight`` is a valid position, the
        borders of that cell are drawn in bright yellow."""
        hr, hc = (None, None)
        if highlight is not None and 0 <= highlight < BOARD_CELLS:
            hr, hc = divmod(highlight, GRID_SIZE)
        top = self._hline("┌", "┬", "┐", "─", highlight_col=hc if hr == 0 else None)
        bot = self._hline(
            "└", "┴", "┘", "─", highlight_col=hc if hr == GRID_SIZE - 1 else None
        )

        lines = [top]

        for row in range(GRID_SIZE):
            cells = [self.cells[row * GRID_SIZE + col] for col in range(GRID_SIZE)]

            # Build each of the 4 content rows for this grid row
            row_renderers = [
                self._render_row1,
                self._render_row2,
                self._render_row3,
                self._render_row4,
            ]

            row_hl = hc if row == hr else None
            for render_idx, renderer in enumerate(row_renderers):
                parts = []
                for col, card in enumerate(cells):
                    pos = row * GRID_SIZE + col
                    if card is None:
                        # Show position number only on the middle row
                        if render_idx == 2:
                            element = self.elements[pos]
                            parts.append(self._render_empty(pos, element))
                        else:
                            parts.append(" " * self.CELL_W)
                    else:
                        parts.append(renderer(card))

                if row_hl is None:
                    sep = Color.border("│")
                    lines.append(sep + sep.join(parts) + sep)
                else:
                    seps = [Color.border("│")] * (GRID_SIZE + 1)
                    seps[row_hl] = Color.highlight("│")
                    seps[row_hl + 1] = Color.highlight("│")
                    lines.append(
                        seps[0]
                        + parts[0]
                        + seps[1]
                        + parts[1]
                        + seps[2]
                        + parts[2]
                        + seps[3]
                    )

            if row < GRID_SIZE - 1:
                # Mid line borders rows ``row`` (below) and ``row + 1`` (above).
                hl = hc if (row == hr or row + 1 == hr) else None
                lines.append(self._hline("├", "┼", "┤", "─", highlight_col=hl))

        lines.append(bot)
        return "\n".join(lines)
