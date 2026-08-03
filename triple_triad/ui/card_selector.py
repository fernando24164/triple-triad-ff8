from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ..models.card import Card
from ..synth.sfx import play_confirm, play_cursor
from .position_selector import QuitGameError

if TYPE_CHECKING:
    from blessed import Terminal


def select_card(
    hand: list[Card],
    term: Terminal | None,
    use_screen: bool,
    render: Callable[[int], None],
    start: int = 0,
) -> int | None:
    """Interactively pick a card from ``hand`` with the ↑/↓ arrow keys.

    Re-renders via ``render(highlight)`` on every move so the highlighted
    card shows the same inverted-bar style as the main menu. Returns the
    chosen index, or None when not running on a styled terminal (callers
    keep the numeric prompt as the fallback). Raises
    :class:`QuitGameError` when the player presses 'q' to abandon the match.
    """
    if term is None or not use_screen or not hand:
        return None
    cur = max(0, min(start, len(hand) - 1))

    with term.cbreak(), term.hidden_cursor():
        render(cur)
        while True:
            k = term.inkey()
            if not k:
                continue
            name = k.name
            if name == "KEY_UP":
                cur = (cur - 1) % len(hand)
                play_cursor()
                render(cur)
            elif name == "KEY_DOWN":
                cur = (cur + 1) % len(hand)
                play_cursor()
                render(cur)
            elif name == "KEY_ENTER" or k == "\n":
                play_confirm()
                return cur
            elif str(k).lower() == "r":
                render(cur)
            elif str(k).lower() == "q":
                raise QuitGameError
