from triple_triad.deck.shelf import (
    _get_shelf_dir,
    _get_shelf_path,
    _write_shelf,
    deck_exists,
    delete_deck,
    list_decks,
    load_deck,
    save_deck,
    validate_name,
)
from triple_triad.models.card import Card


class TestShelfPaths:
    def test_get_shelf_dir_returns_path(self):
        path = _get_shelf_dir()
        assert path.name == "triple-triad"

    def test_get_shelf_path_ends_with_decks_json(self):
        path = _get_shelf_path()
        assert path.name == "decks.json"
        assert path.parent.name == "triple-triad"


class TestShelfCrud:
    def test_empty_shelf(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        assert list_decks() == []
        assert deck_exists("anything") is False

    def test_save_and_list_decks(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        cards = [
            Card("Geezard"),
            Card("Funguar"),
            Card("Bite Bug"),
            Card("Red Bat"),
            Card("Blobra"),
        ]
        save_deck("test_deck", cards)
        assert list_decks() == ["test_deck"]
        assert deck_exists("test_deck") is True

    def test_save_multiple_decks(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        d1 = [
            Card("Geezard"),
            Card("Funguar"),
            Card("Bite Bug"),
            Card("Red Bat"),
            Card("Blobra"),
        ]
        d2 = [
            Card("Ifrit"),
            Card("Shiva"),
            Card("Carbuncle"),
            Card("Siren"),
            Card("Leviathan"),
        ]
        save_deck("deck_a", d1)
        save_deck("deck_b", d2)
        assert list_decks() == ["deck_a", "deck_b"]

    def test_load_deck(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        cards = [
            Card("Geezard"),
            Card("Funguar"),
            Card("Bite Bug"),
            Card("Red Bat"),
            Card("Blobra"),
        ]
        save_deck("test_deck", cards)
        loaded = load_deck("test_deck")
        assert loaded is not None
        assert len(loaded) == 5
        assert [c.name for c in loaded] == [c.name for c in cards]

    def test_load_nonexistent_returns_none(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        assert load_deck("nope") is None

    def test_delete_deck(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        cards = [
            Card("Geezard"),
            Card("Funguar"),
            Card("Bite Bug"),
            Card("Red Bat"),
            Card("Blobra"),
        ]
        save_deck("test_deck", cards)
        assert deck_exists("test_deck") is True
        assert delete_deck("test_deck") is True
        assert deck_exists("test_deck") is False
        assert list_decks() == []

    def test_delete_nonexistent_returns_false(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        assert delete_deck("nope") is False

    def test_overwrite_deck(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        d1 = [
            Card("Geezard"),
            Card("Funguar"),
            Card("Bite Bug"),
            Card("Red Bat"),
            Card("Blobra"),
        ]
        d2 = [
            Card("Ifrit"),
            Card("Shiva"),
            Card("Carbuncle"),
            Card("Siren"),
            Card("Leviathan"),
        ]
        save_deck("deck", d1)
        save_deck("deck", d2)
        loaded = load_deck("deck")
        assert loaded is not None
        assert loaded[0].name == "Ifrit"

    def test_load_deck_with_wrong_size_returns_none(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        _write_shelf({"bad_deck": ["Geezard", "Funguar"]})
        assert load_deck("bad_deck") is None

    def test_load_deck_with_invalid_card_returns_none(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        names = ["Geezard", "Funguar", "Bite Bug", "Red Bat", "NonExistentCard"]
        _write_shelf({"bad_deck": names})
        assert load_deck("bad_deck") is None

    def test_corrupt_shelf_treated_as_empty(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        shelf_file.write_text("this is not json", encoding="utf-8")
        assert list_decks() == []

    def test_non_dict_shelf_treated_as_empty(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        shelf_file.write_text("[]", encoding="utf-8")
        assert list_decks() == []

    def test_missing_file_returns_empty(self, monkeypatch, tmp_path):
        shelf_file = tmp_path / "nonexistent" / "decks.json"
        monkeypatch.setattr(
            "triple_triad.deck.shelf._get_shelf_path", lambda: shelf_file
        )
        assert list_decks() == []


class TestValidateName:
    def test_empty_name(self):
        assert validate_name("") is not None
        assert validate_name("   ") is not None

    def test_valid_name(self):
        assert validate_name("My Deck") is None
        assert validate_name("Fire Power 2024") is None

    def test_name_too_long(self):
        assert validate_name("A" * 81) is not None
        assert validate_name("A" * 80) is None

    def test_forbidden_chars(self):
        for ch in '/\\<>:"|?*':
            assert validate_name(f"deck{ch}name") is not None

    def test_valid_with_hyphen_and_underscore(self):
        assert validate_name("my-fire_deck-v2") is None
