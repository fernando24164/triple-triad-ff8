from unittest.mock import MagicMock

import pytest

from triple_triad.models.card import Card
from triple_triad.ui.card_selector import select_card
from triple_triad.ui.position_selector import QuitGameError


class _Key:
    def __init__(self, name=None, value=""):
        self.name = name
        self._value = value

    def __str__(self):
        return self._value

    def __eq__(self, other):
        return self._value == other


def _hand() -> list[Card]:
    return [Card("Geezard"), Card("Funguar"), Card("Bite Bug")]


class TestSelectCard:
    def test_returns_first_card_on_enter(self):
        term = MagicMock()
        term.inkey.side_effect = [_Key("KEY_ENTER")]
        assert select_card(_hand(), term, True, lambda h: None) == 0

    def test_arrow_down_moves_selection(self):
        term = MagicMock()
        term.inkey.side_effect = [_Key("KEY_DOWN"), _Key("KEY_DOWN"), _Key("KEY_ENTER")]
        assert select_card(_hand(), term, True, lambda h: None) == 2

    def test_arrow_up_moves_selection(self):
        term = MagicMock()
        term.inkey.side_effect = [_Key("KEY_UP"), _Key("KEY_ENTER")]
        assert select_card(_hand(), term, True, lambda h: None) == 2

    def test_wraps_around_edges(self):
        term = MagicMock()
        term.inkey.side_effect = [_Key("KEY_UP"), _Key("KEY_UP"), _Key("KEY_ENTER")]
        assert select_card(_hand(), term, True, lambda h: None) == 1

    def test_renders_on_every_move(self):
        term = MagicMock()
        term.inkey.side_effect = [_Key("KEY_DOWN"), _Key("KEY_ENTER")]
        rendered = []
        select_card(_hand(), term, True, rendered.append)
        assert rendered == [0, 1]

    def test_quit_raises(self):
        term = MagicMock()
        term.inkey.side_effect = [_Key(value="q")]
        with pytest.raises(QuitGameError):
            select_card(_hand(), term, True, lambda h: None)

    def test_non_screen_returns_none(self):
        assert select_card(_hand(), None, False, lambda h: None) is None

    def test_empty_hand_returns_none(self):
        term = MagicMock()
        assert select_card([], term, True, lambda h: None) is None
