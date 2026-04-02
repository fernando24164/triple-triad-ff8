import pytest
from triple_triad.cards import Card
from triple_triad.board import Board


@pytest.fixture
def sample_card():
    """Return a sample card for testing."""
    return Card("Geezard")


@pytest.fixture
def sample_cards():
    """Return a list of sample cards for testing."""
    return [Card("Geezard"), Card("Funguar"), Card("Bite Bug"), Card("Red Bat"), Card("Blobra")]


@pytest.fixture
def player_hand():
    """Return a player hand with 5 cards."""
    cards = [Card("Geezard"), Card("Funguar"), Card("Bite Bug"), Card("Red Bat"), Card("Blobra")]
    for card in cards:
        card.owner = "P"
    return cards


@pytest.fixture
def cpu_hand():
    """Return a CPU hand with 5 cards."""
    cards = [Card("Grat"), Card("Buel"), Card("Mesmerize"), Card("Glacial Eye"), Card("Belhelmel")]
    for card in cards:
        card.owner = "CPU"
    return cards


@pytest.fixture
def empty_board():
    """Return an empty board."""
    return Board()


@pytest.fixture
def board_with_cards():
    """Return a board with some cards placed."""
    board = Board()
    card1 = Card("Geezard")
    card1.owner = "P"
    card2 = Card("Funguar")
    card2.owner = "CPU"
    board.place(0, card1)
    board.place(1, card2)
    return board


@pytest.fixture
def full_board():
    """Return a full board with all 9 cards."""
    board = Board()
    card_names = ["Geezard", "Funguar", "Bite Bug", "Red Bat", "Blobra", 
                  "Gayla", "Gesper", "Fastitocalon", "Blood Soul"]
    for i, name in enumerate(card_names):
        card = Card(name)
        card.owner = "P" if i % 2 == 0 else "CPU"
        board.place(i, card)
    return board


@pytest.fixture
def basic_rules():
    """Return empty rules set (basic rules)."""
    return set()


@pytest.fixture
def same_rules():
    """Return rules with Same enabled."""
    return {"Same"}


@pytest.fixture
def plus_rules():
    """Return rules with Plus enabled."""
    return {"Plus"}


@pytest.fixture
def all_rules():
    """Return rules with all optional rules enabled."""
    return {"Open", "Same", "Plus", "Random"}
