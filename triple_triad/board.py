# triple_triad/board.py


class Color:
    """ANSI color codes for terminal rendering."""

    RESET = "\033[0m"
    # Card ownership
    P_FG = "\033[92m"  # bright green  — player
    CPU_FG = "\033[91m"  # bright red    — CPU
    # Board structure
    BORDER = "\033[90m"  # dark grey     — grid lines
    EMPTY_POS = "\033[33m"  # yellow        — empty cell number

    @staticmethod
    def player(text: str) -> str:
        return f"{Color.P_FG}{text}{Color.RESET}"

    @staticmethod
    def cpu(text: str) -> str:
        return f"{Color.CPU_FG}{text}{Color.RESET}"

    @staticmethod
    def border(text: str) -> str:
        return f"{Color.BORDER}{text}{Color.RESET}"

    @staticmethod
    def empty(text: str) -> str:
        return f"{Color.EMPTY_POS}{text}{Color.RESET}"

    @staticmethod
    def card(text: str, owner: str) -> str:
        """Color a string based on card owner ('P' or 'CPU')."""
        if owner == "P":
            return Color.player(text)
        return Color.cpu(text)


class Board:
    """3x3 grid. Positions 0-8 (row-major)."""

    CELL_W = 18  # inner width of each cell (visible characters only)

    def __init__(self):
        self.cells = [None] * 9  # Card or None

    def place(self, pos, card):
        self.cells[pos] = card

    def is_empty(self, pos):
        return self.cells[pos] is None

    def get_neighbors(self, pos):
        """Return dict of direction -> (neighbor_pos, neighbor_card)."""
        row, col = divmod(pos, 3)
        neighbors = {}
        if row > 0:
            neighbors["top"] = (pos - 3, self.cells[pos - 3])
        if row < 2:
            neighbors["bottom"] = (pos + 3, self.cells[pos + 3])
        if col > 0:
            neighbors["left"] = (pos - 1, self.cells[pos - 1])
        if col < 2:
            neighbors["right"] = (pos + 1, self.cells[pos + 1])
        return neighbors

    # ── Per-cell row renderers ─────────────────────────────────────────────
    # Each method returns a string of exactly CELL_W *visible* characters.
    # ANSI codes are injected AFTER the plain-text layout is built, so
    # padding/alignment is always calculated on raw strings first.

    @staticmethod
    def _render_row1(card) -> str:
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
    def _render_row2(card) -> str:
        """Top value centered with up-arrow."""
        w = Board.CELL_W
        if card is None:
            return " " * w
        plain = f"{'▲ ' + str(card.top):^{w}}"
        return Color.card(plain, card.owner)

    @staticmethod
    def _render_row3(card) -> str:
        """Left value — element — right value, all on one line."""
        w = Board.CELL_W
        if card is None:
            return " " * w

        el = card.element[:3] if card.element else "   "

        left_str = f"◀ {card.left}"
        right_str = f"{card.right} ▶"

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
    def _render_row4(card) -> str:
        """Bottom value centered with down-arrow."""
        w = Board.CELL_W
        if card is None:
            return " " * w
        plain = f"{'▼ ' + str(card.bottom):^{w}}"
        return Color.card(plain, card.owner)

    @staticmethod
    def _render_empty(pos: int) -> str:
        """Empty cell: show position number centred on row 3."""
        w = Board.CELL_W
        label = f"[ {pos + 1} ]"
        plain = f"{label:^{w}}"
        return Color.empty(plain)

    # ── Border helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _colored_border(text: str) -> str:
        return Color.border(text)

    @classmethod
    def _hline(cls, left: str, mid: str, right: str, fill: str) -> str:
        segment = fill * cls.CELL_W
        line = left + (mid.join([segment] * 3)) + right
        return cls._colored_border(line)

    # ── Main renderer ──────────────────────────────────────────────────────

    def display(self) -> str:
        top = self._hline("┌", "┬", "┐", "─")
        mid = self._hline("├", "┼", "┤", "─")
        bot = self._hline("└", "┴", "┘", "─")
        sep = Color.border("│")

        lines = [top]

        for row in range(3):
            cells = [self.cells[row * 3 + col] for col in range(3)]

            # Build each of the 4 content rows for this grid row
            row_renderers = [
                self._render_row1,
                self._render_row2,
                self._render_row3,
                self._render_row4,
            ]

            for render_idx, renderer in enumerate(row_renderers):
                parts = []
                for col, card in enumerate(cells):
                    pos = row * 3 + col
                    if card is None:
                        # Show position number only on the middle row
                        if render_idx == 2:
                            parts.append(self._render_empty(pos))
                        else:
                            parts.append(" " * self.CELL_W)
                    else:
                        parts.append(renderer(card))

                lines.append(sep + sep.join(parts) + sep)

            if row < 2:
                lines.append(mid)

        lines.append(bot)
        return "\n".join(lines)