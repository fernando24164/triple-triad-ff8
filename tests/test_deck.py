from triple_triad.data.cards import CARDS
from triple_triad.deck.builder import (
    DIFFICULTY_CONFIG,
    build_cpu_deck,
    build_random_deck,
    build_starter_deck,
    get_cpu_ai_mode,
)
from triple_triad.deck.picker import _filter_cards, _sort_cards
from triple_triad.deck.presets import DECK_PRESETS, build_preset_deck, list_presets
from triple_triad.models.card import Card


class TestDeck:
    """Test the deck building logic."""

    def test_build_starter_deck(self):
        """Test building a starter deck."""
        deck = build_starter_deck()
        assert len(deck) == 5
        assert all(isinstance(card, Card) for card in deck)
        # All cards should be level 3 or lower
        assert all(card.level <= 3 for card in deck)

    def test_build_starter_deck_unique(self):
        """Test that starter deck has unique cards."""
        deck = build_starter_deck()
        card_names = [card.name for card in deck]
        assert len(card_names) == len(set(card_names))

    def test_build_cpu_deck_easy(self):
        """Test building CPU deck for easy difficulty."""
        deck = build_cpu_deck("easy")
        assert len(deck) == 5
        assert all(isinstance(card, Card) for card in deck)
        # Easy difficulty: CPU uses cards level 1-3
        assert all(1 <= card.level <= 3 for card in deck)

    def test_build_cpu_deck_medium(self):
        """Test building CPU deck for medium difficulty."""
        deck = build_cpu_deck("medium")
        assert len(deck) == 5
        assert all(isinstance(card, Card) for card in deck)
        # Medium difficulty: CPU uses cards level 4-6
        assert all(4 <= card.level <= 6 for card in deck)

    def test_build_cpu_deck_hard(self):
        """Test building CPU deck for hard difficulty."""
        deck = build_cpu_deck("hard")
        assert len(deck) == 5
        assert all(isinstance(card, Card) for card in deck)
        # Hard difficulty: CPU uses cards level 7-9
        assert all(7 <= card.level <= 9 for card in deck)

    def test_build_cpu_deck_invalid_difficulty(self):
        """Test building CPU deck with invalid difficulty defaults to medium."""
        deck = build_cpu_deck("invalid")
        assert len(deck) == 5
        # Should default to medium difficulty (level 4-6)
        assert all(4 <= card.level <= 6 for card in deck)

    def test_build_cpu_deck_unique(self):
        """Test that CPU deck has unique cards."""
        deck = build_cpu_deck("medium")
        card_names = [card.name for card in deck]
        assert len(card_names) == len(set(card_names))

    def test_get_cpu_ai_mode_easy(self):
        """Test getting AI mode for easy difficulty."""
        mode = get_cpu_ai_mode("easy")
        assert mode == "random"

    def test_get_cpu_ai_mode_medium(self):
        """Test getting AI mode for medium difficulty."""
        mode = get_cpu_ai_mode("medium")
        assert mode == "greedy"

    def test_get_cpu_ai_mode_hard(self):
        """Test getting AI mode for hard difficulty."""
        mode = get_cpu_ai_mode("hard")
        assert mode == "greedy"

    def test_get_cpu_ai_mode_invalid(self):
        """Test getting AI mode for invalid difficulty defaults to medium."""
        mode = get_cpu_ai_mode("invalid")
        assert mode == "greedy"  # Medium difficulty uses greedy

    def test_difficulty_config_structure(self):
        """Test that difficulty config has correct structure."""
        for difficulty in ["easy", "medium", "hard"]:
            cfg = DIFFICULTY_CONFIG[difficulty]
            assert "player_max_level" in cfg
            assert "cpu_min_level" in cfg
            assert "cpu_max_level" in cfg
            assert "cpu_ai" in cfg
            assert "description" in cfg
            assert cfg["player_max_level"] == 9
            assert 1 <= cfg["cpu_min_level"] <= cfg["cpu_max_level"] <= 9
            assert cfg["cpu_ai"] in ["random", "greedy"]

    def test_filter_cards_by_level(self):
        """Test filtering cards by level range."""
        all_names = sorted(CARDS.keys())
        for level in range(1, 10):
            results = _filter_cards(all_names, level_range=(level, level))
            assert len(results) > 0
            assert all(CARDS[name].level == level for name in results)

    def test_filter_cards_by_level_range(self):
        """Test filtering cards by level range."""
        all_names = sorted(CARDS.keys())
        results = _filter_cards(all_names, level_range=(1, 3))
        assert all(1 <= CARDS[name].level <= 3 for name in results)

    def test_filter_cards_by_element(self):
        """Test filtering cards by element."""
        all_names = sorted(CARDS.keys())
        results = _filter_cards(all_names, element="Fire")
        assert len(results) > 0
        assert all(
            CARDS[name].element and CARDS[name].element.value == "Fire"
            for name in results
        )

    def test_filter_cards_combined(self):
        """Test filtering cards by level and element combined."""
        all_names = sorted(CARDS.keys())
        results = _filter_cards(all_names, level_range=(1, 5), element="Thunder")
        assert all(1 <= CARDS[name].level <= 5 for name in results)
        assert all(
            CARDS[name].element and CARDS[name].element.value == "Thunder"
            for name in results
        )

    def test_sort_cards_by_level(self):
        """Test sorting cards by level."""
        all_names = sorted(CARDS.keys())
        sorted_names = _sort_cards(all_names, "level")
        levels = [CARDS[n].level for n in sorted_names]
        assert levels == sorted(levels)

    def test_sort_cards_by_name(self):
        """Test sorting cards by name."""
        all_names = list(CARDS.keys())
        sorted_names = _sort_cards(all_names, "name")
        assert sorted_names == sorted(all_names)

    def test_sort_cards_by_stat(self):
        """Test sorting cards by a stat (top)."""
        all_names = list(CARDS.keys())
        sorted_names = _sort_cards(all_names, "top")
        tops = [CARDS[n].top for n in sorted_names]
        assert tops == sorted(tops, reverse=True)

    # ── Preset deck tests ─────────────────────────────────────────────

    def test_list_presets(self):
        """Test listing available presets."""
        presets = list_presets()
        assert len(presets) > 0
        assert all(isinstance(p, str) for p in presets)

    def test_build_preset_deck(self):
        """Test building a deck from a preset."""
        for preset_name in list_presets():
            deck = build_preset_deck(preset_name)
            assert len(deck) == 5
            assert all(isinstance(card, Card) for card in deck)
            # All cards should be unique
            names = [c.name for c in deck]
            assert len(names) == len(set(names))

    def test_build_preset_deck_invalid(self):
        """Test building a deck from an invalid preset."""
        import pytest

        with pytest.raises(ValueError):
            build_preset_deck("NonExistentPreset")

    def test_deck_presets_valid_cards(self):
        """Test that all cards in presets exist in the card database."""
        for preset_name, card_names in DECK_PRESETS.items():
            for name in card_names:
                assert name in CARDS, (
                    f"Card '{name}' in preset '{preset_name}' not found in CARDS"
                )

    def test_build_random_deck(self):
        """Test building a random deck."""
        deck = build_random_deck()
        assert len(deck) == 5
        assert all(isinstance(card, Card) for card in deck)
        names = [c.name for c in deck]
        assert len(names) == len(set(names))

    def test_all_cards_in_database(self):
        """Test that all cards in CARDS dictionary are valid."""
        from triple_triad.data.cards import CardStats, Element

        for name, stats in CARDS.items():
            assert isinstance(name, str)
            assert isinstance(stats, CardStats)
            assert 1 <= stats.top <= 10
            assert 1 <= stats.right <= 10
            assert 1 <= stats.bottom <= 10
            assert 1 <= stats.left <= 10
            assert stats.element is None or isinstance(stats.element, Element)
            assert 1 <= stats.level <= 9
