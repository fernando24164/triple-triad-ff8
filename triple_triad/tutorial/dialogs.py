import time
from typing import Any

from blessed import Terminal

from ..synth.sfx import play_cancel, play_confirm

term = Terminal()

DIALOG_W = 64
SPEAKER_LABEL = "♕ Queen of Cards"


def _center_x(text: str) -> int:
    return max(0, (term.width - term.length(text)) // 2)


def _wrap_text(text: str, width: int) -> list[str]:
    """Wrap text to fit inside a box of given inner width."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def show_dialog(
    lines: list[str],
    speaker: str = SPEAKER_LABEL,
    width: int = DIALOG_W,
) -> bool:
    """Display a dialog box with typewriter text effect.

    Args:
        lines: Text lines to display (auto-wrapped).
        speaker: Name shown in the dialog header.
        width: Total width of the dialog box (including borders).

    Returns:
        True if user pressed Enter to advance, False if they quit with 'q'.
    """
    inner_w = width - 4
    wrapped: list[str] = []
    for line in lines:
        if line == "":
            wrapped.append("")
        else:
            wrapped.extend(_wrap_text(line, inner_w))

    box_h = len(wrapped) + 5
    box_y = max(2, (term.height - box_h) // 2)
    box_x = _center_x(" " * width)
    text_start_y = box_y + 3

    typed_chars = 0
    total_chars = sum(len(line) for line in wrapped)

    header = f" {speaker} "
    bar = "─" * (width - 2 - len(header))

    _draw_box(box_x, box_y, width, box_h, header, bar)
    _clear_text_area(box_x, text_start_y, inner_w, len(wrapped))
    for i, wline in enumerate(wrapped):
        y = text_start_y + i
        line_to_print = ""
        for ch in wline:
            line_to_print += ch
            x = box_x + 2
            printed = line_to_print.ljust(inner_w)
            print(
                term.move_yx(y, x) + term.white(printed) + term.normal,
                end="",
                flush=True,
            )
            typed_chars += 1
            progress = typed_chars / total_chars
            delay = max(0.005, 0.03 - progress * 0.02)
            time.sleep(delay)

    _show_prompt(box_x, box_y, box_h, width)

    while True:
        k: Any = term.inkey(timeout=0.1)
        if not k:
            continue
        if str(k).lower() == "q":
            play_cancel()
            return False
        if k.name == "KEY_ENTER" or k == "\n":
            play_confirm()
            return True


def _draw_box(
    box_x: int, box_y: int, width: int, box_h: int, header: str, bar: str
) -> None:
    print(term.move_yx(box_y, box_x) + term.cyan + f"╔{header}{bar}╗" + term.normal)
    for y in range(box_y + 1, box_y + box_h - 1):
        print(term.move_yx(y, box_x) + term.cyan + "║" + term.normal, end="")
        print(term.move_yx(y, box_x + width - 1) + term.cyan + "║" + term.normal)
    print(
        term.move_yx(box_y + box_h - 1, box_x)
        + term.cyan
        + f"╚{'═' * (width - 2)}╝"
        + term.normal
    )


def _clear_text_area(box_x: int, start_y: int, inner_w: int, count: int) -> None:
    blank = " " * inner_w
    for i in range(count):
        print(term.move_yx(start_y + i, box_x + 2) + blank)


def _show_prompt(box_x: int, box_y: int, box_h: int, width: int) -> None:
    prompt = "Press Enter to continue  ·  q to skip"
    px = box_x + width - len(prompt) - 3
    py = box_y + box_h - 2
    print(term.move_yx(py, px) + term.dim + prompt + term.normal)
