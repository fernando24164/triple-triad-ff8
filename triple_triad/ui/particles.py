from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..constants import GRID_SIZE
from ..models.card import Card
from .render import CELL_W

if TYPE_CHECKING:
    from blessed import Terminal


@dataclass
class _Particle:
    r: float
    c: float
    vx: float
    vy: float
    char: str
    shade: str


_GREEN = "\033[92;1m"
_GREEN_DIM = "\033[32m"
_GREEN_256_A = "\033[38;5;82m"
_GREEN_256_B = "\033[38;5;46m"
_GREEN_256_C = "\033[38;5;118m"
_RESET = "\033[0m"

_GREEN_SHADES: tuple[str, ...] = (
    _GREEN,
    _GREEN_256_A,
    _GREEN_256_B,
    _GREEN_256_C,
    _GREEN_DIM,
)

_PARTICLE_CHARS: tuple[str, ...] = ("•", "·", "∙", "*", "✦", "∘", "✱", "+")

_PARTICLES_PER_CELL = 10
_FRAMES = 14
_FRAME_DT = 0.045
_GRAVITY = 0.18


def _cell_origin(pos: int) -> tuple[int, int]:
    row, col = divmod(pos, GRID_SIZE)
    row_start = 1 + row * 5
    col_start = 1 + col * (CELL_W + 1)
    return row_start, col_start


def _place_single(
    term: Terminal, cursor_row: int, row: int, col: int, content: str
) -> str:
    up = cursor_row - row
    return (
        term.move_up(up)
        + term.move_x(col)  # type: ignore[arg-type]
        + content
        + term.move_x(0)  # type: ignore[arg-type]
        + term.move_down(up)
    )


def show_capture_particles(
    term: Terminal | None,
    cursor_row: int,
    captures: list[tuple[int, Card]],
    col_offset: int = 0,
    *,
    color_shades: tuple[str, ...] | None = None,
) -> None:
    """Burst green particles outward from each captured cell.

    No-op when no interactive terminal is available or there are no
    captures.  Particles are drawn via relative cursor moves (same
    technique as ``capture_fx._paint``) so they overlay the board
    without needing the absolute screen origin.

    Args:
        term: Active blessed Terminal, or None.
        cursor_row: Lines from board top border to cursor (as returned
            by ``render_turn_screen``).
        captures: (pos, card) pairs being captured this turn.
        col_offset: Horizontal board centering offset.
        color_shades: Optional override for particle colors.
    """
    if term is None or not term.does_styling or not captures:
        return

    shades = color_shades if color_shades is not None else _GREEN_SHADES

    particles: list[_Particle] = []
    for pos, _ in captures:
        cell_r, cell_c = _cell_origin(pos)
        centre_r = float(cell_r + 1)  # vertical centre (between the 4 rows)
        centre_c = float(cell_c + CELL_W // 2)
        for _ in range(_PARTICLES_PER_CELL):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.55, 2.4)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed * 0.55
            ch: str = random.choice(_PARTICLE_CHARS)
            shade = (
                random.choice(shades[:3])
                if random.random() < 0.7
                else random.choice(shades)
            )
            particles.append(
                _Particle(
                    r=centre_r,
                    c=centre_c,
                    vx=vx,
                    vy=vy,
                    char=ch,
                    shade=shade,
                )
            )

    prev_cells: set[tuple[int, int]] = set()

    for frame in range(_FRAMES):
        progress = frame / max(1, _FRAMES - 1)

        frame_out = ""
        for pr, pc in prev_cells:
            abs_col = pc + col_offset
            if 0 <= abs_col < term.width:
                frame_out += _place_single(term, cursor_row, pr, abs_col, " ")

        new_cells: set[tuple[int, int]] = set()
        for p in particles:
            p.r += p.vy
            p.c += p.vx
            p.vy += _GRAVITY
            p.vx *= 0.97

            ir = int(round(p.r))
            ic = int(round(p.c))
            abs_col = ic + col_offset
            if abs_col < 0 or abs_col >= term.width:
                continue
            shade = p.shade
            ch = p.char
            if progress > 0.65:
                shade = _GREEN_DIM
                if ch not in ("·", "∙", "."):
                    ch = "·"
            elif progress > 0.35:
                if random.random() < 0.25:
                    shade = _GREEN_DIM

            if (ir, ic) in new_cells:
                continue
            new_cells.add((ir, ic))
            frame_out += _place_single(
                term, cursor_row, ir, abs_col, f"{shade}{ch}{_RESET}"
            )

        if frame_out:
            print(frame_out, end="", flush=True)
        time.sleep(_FRAME_DT)
        prev_cells = new_cells

    if prev_cells:
        clear_out = ""
        for pr, pc in prev_cells:
            abs_col = pc + col_offset
            if 0 <= abs_col < term.width:
                clear_out += _place_single(term, cursor_row, pr, abs_col, " ")
        if clear_out:
            print(clear_out, end="", flush=True)
