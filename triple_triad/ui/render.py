from collections.abc import Callable

from ..constants import BOARD_CELLS, GRID_SIZE
from ..data.cards import Element
from ..models.board import Board
from ..models.card import Card, stat_display
from .color import Color

CELL_W = 18  # inner width of each cell (visible characters only)


def board_total_width() -> int:
    """Visible width (chars) of one line from ``render_board``."""
    return GRID_SIZE * (CELL_W + 1) + 1


# ── Per-cell row renderers ───────────────────────────────────────────────────
# Each function returns a string of exactly CELL_W *visible* characters.
# ANSI codes are injected AFTER the plain-text layout is built, so
# padding/alignment is always calculated on raw strings first.


def render_row1(card: Card | None) -> str:
    """Owner symbol + card name, left-aligned."""
    w = CELL_W
    if card is None:
        return " " * w
    sym = "■" if card.owner == "P" else "□"
    label = f"{sym}{card.name}"
    label = label[: w - 1]  # truncate to visible width
    plain = f" {label:<{w - 1}}"  # exactly CELL_W visible chars
    return Color.card(plain, card.owner)


def render_row2(card: Card | None) -> str:
    """Top value centered with up-arrow."""
    w = CELL_W
    if card is None:
        return " " * w
    plain = f"{'▲ ' + stat_display(card.top):^{w}}"
    return Color.card(plain, card.owner)


def render_row3(card: Card | None) -> str:
    """Left value — element — right value, all on one line."""
    w = CELL_W
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


def render_row4(card: Card | None) -> str:
    """Bottom value centered with down-arrow."""
    w = CELL_W
    if card is None:
        return " " * w
    plain = f"{'▼ ' + stat_display(card.bottom):^{w}}"
    return Color.card(plain, card.owner)


def _render_empty(pos: int, element: Element | None = None) -> str:
    """Empty cell: show position number centred on row 3."""
    w = CELL_W
    if element:
        el_abbr = element.value[:3]
        label = f"[{pos + 1}] {el_abbr}"
    else:
        label = f"[ {pos + 1} ]"
    plain = f"{label:^{w}}"
    return Color.empty(plain)


# ── Border helpers ───────────────────────────────────────────────────────────


def _hline(
    left: str,
    mid: str,
    right: str,
    fill: str,
    highlight_col: int | None = None,
) -> str:
    segment = fill * CELL_W
    line = left + (mid.join([segment] * GRID_SIZE)) + right
    if highlight_col is None or not 0 <= highlight_col < GRID_SIZE:
        return Color.border(line)
    # Span covering the segment of the highlighted column plus the
    # junction chars on both of its ends.
    span_start = highlight_col * (CELL_W + 1)
    span_end = span_start + CELL_W + 1
    return (
        Color.border(line[:span_start])
        + Color.highlight(line[span_start:span_end])
        + Color.border(line[span_end:])
    )


_ROW_RENDERERS: tuple[Callable[[Card | None], str], ...] = (
    render_row1,
    render_row2,
    render_row3,
    render_row4,
)


# ── Main renderer ────────────────────────────────────────────────────────────


def render_board(board: Board, highlight: int | None = None) -> str:
    """Render the board. When ``highlight`` is a valid position, the
    borders of that cell are drawn in bright yellow."""
    hr, hc = (None, None)
    if highlight is not None and 0 <= highlight < BOARD_CELLS:
        hr, hc = divmod(highlight, GRID_SIZE)
    top = _hline("┌", "┬", "┐", "─", highlight_col=hc if hr == 0 else None)
    bot = _hline(
        "└", "┴", "┘", "─", highlight_col=hc if hr == GRID_SIZE - 1 else None
    )

    lines = [top]

    for row in range(GRID_SIZE):
        cells = [board.cells[row * GRID_SIZE + col] for col in range(GRID_SIZE)]

        row_hl = hc if row == hr else None
        for render_idx, renderer in enumerate(_ROW_RENDERERS):
            parts = []
            for col, card in enumerate(cells):
                pos = row * GRID_SIZE + col
                if card is None:
                    # Show position number only on the middle row
                    if render_idx == 2:
                        element = board.elements[pos]
                        parts.append(_render_empty(pos, element))
                    else:
                        parts.append(" " * CELL_W)
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
            lines.append(_hline("├", "┼", "┤", "─", highlight_col=hl))

    lines.append(bot)
    return "\n".join(lines)
