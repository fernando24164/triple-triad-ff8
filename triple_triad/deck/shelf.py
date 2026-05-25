import json
import os
import sys
from pathlib import Path

from ..constants import DECK_SIZE
from ..data.cards import CARDS
from ..models.card import Card


def _get_shelf_dir() -> Path:
    if sys.platform == "linux":
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home() / ".triple-triad"
    return base / "triple-triad"


def _get_shelf_path() -> Path:
    return _get_shelf_dir() / "decks.json"


def _read_shelf() -> dict[str, list[str]]:
    path = _get_shelf_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {
                k: v
                for k, v in data.items()
                if isinstance(k, str) and isinstance(v, list)
            }
        return {}
    except (json.JSONDecodeError, OSError):
        return {}


def _write_shelf(decks: dict[str, list[str]]) -> None:
    path = _get_shelf_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(decks, indent=2, ensure_ascii=False), encoding="utf-8")


def list_decks() -> list[str]:
    return sorted(_read_shelf().keys())


def deck_exists(name: str) -> bool:
    return name in _read_shelf()


def load_deck(name: str) -> list[Card] | None:
    shelf = _read_shelf()
    card_names = shelf.get(name)
    if card_names is None:
        return None
    validated: list[Card] = []
    for cn in card_names:
        if cn in CARDS:
            validated.append(Card(cn))
    if len(validated) != DECK_SIZE:
        return None
    return validated


def save_deck(name: str, cards: list[Card]) -> None:
    shelf = _read_shelf()
    shelf[name] = [c.name for c in cards]
    _write_shelf(shelf)


def delete_deck(name: str) -> bool:
    shelf = _read_shelf()
    if name not in shelf:
        return False
    del shelf[name]
    _write_shelf(shelf)
    return True


def validate_name(name: str) -> str | None:
    stripped = name.strip()
    if not stripped:
        return "Deck name cannot be empty."
    if len(stripped) > 80:
        return "Deck name must be 80 characters or fewer."
    forbidden = set('/\\<>:"|?*')
    if any(c in forbidden for c in stripped):
        return 'Deck name cannot contain / \\ < > : " | ? *'
    return None
