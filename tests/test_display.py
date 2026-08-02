from unittest.mock import MagicMock

from triple_triad.models.card import Card
from triple_triad.ui.display import display_hand


def _term() -> MagicMock:
    term = MagicMock()
    term.does_styling = True
    term.width = 120
    term.bold_black_on_cyan.side_effect = lambda s: f"<hl>{s}</hl>"
    return term


def _hand() -> list[Card]:
    return [Card("Geezard"), Card("Funguar")]


class TestDisplayHand:
    def test_no_highlight_by_default(self, capsys):
        display_hand(_hand(), "Your")
        out = capsys.readouterr().out
        assert "<hl>" not in out

    def test_highlights_selected_card(self, capsys):
        display_hand(_hand(), "Your", term=_term(), highlight=1)
        out = capsys.readouterr().out
        assert "<hl>" in out
        assert out.count("<hl>") == 1
        assert "Funguar" in out
        assert "Geezard" not in out[out.index("<hl>") :]

    def test_highlight_respects_show_false(self, capsys):
        display_hand(_hand(), "Your", show=False, term=_term(), highlight=0)
        out = capsys.readouterr().out
        assert "<hl>" in out
        assert "???" in out
