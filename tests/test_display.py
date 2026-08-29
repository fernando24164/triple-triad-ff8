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
        # Boxed hand highlights the whole box (index + 6 box rows) -> 7 segments
        assert out.count("<hl>") == 7
        assert "Funguar" in out
        # Funguar must appear inside a highlighted segment
        assert any("Funguar" in seg for seg in out.split("<hl>")[1:])
        # Geezard must not appear inside any highlighted segment
        highlighted_segments = [seg.split("</hl>")[0] for seg in out.split("<hl>")[1:]]
        assert all("Geezard" not in seg for seg in highlighted_segments)
        assert "Geezard" in out

    def test_highlight_respects_show_false(self, capsys):
        display_hand(_hand(), "Your", show=False, term=_term(), highlight=0)
        out = capsys.readouterr().out
        assert "<hl>" in out
        assert "???" in out
