from triple_triad.cards import Card, CARDS


class TestCard:
    """Test the Card class."""

    def test_card_creation(self, sample_card):
        """Test that a card is created with correct attributes."""
        assert sample_card.name == "Geezard"
        assert sample_card.top == 1
        assert sample_card.right == 4
        assert sample_card.bottom == 1
        assert sample_card.left == 5
        assert sample_card.element is None
        assert sample_card.level == 1
        assert sample_card.owner is None

    def test_card_with_element(self):
        """Test that a card with an element is created correctly."""
        card = Card("Gayla")
        assert card.name == "Gayla"
        assert card.element == "Thunder"
        assert card.level == 2

    def test_card_str(self, sample_card):
        """Test the string representation of a card."""
        result = str(sample_card)
        assert "Geezard" in result
        assert "T:1" in result
        assert "R:4" in result
        assert "B:1" in result
        assert "L:5" in result
        assert "Lv:1" in result

    def test_card_str_with_element(self):
        """Test the string representation of a card with an element."""
        card = Card("Gayla")
        result = str(card)
        assert "Gayla" in result
        assert "[Thunder]" in result

    def test_card_short_str(self, sample_card):
        """Test the short string representation."""
        result = sample_card.short_str()
        assert "Geezard" in result

    def test_card_short_str_with_owner(self, sample_card):
        """Test the short string representation with owner."""
        sample_card.owner = "P"
        result = sample_card.short_str()
        assert "■" in result  # Player symbol
        assert "Geezard" in result

    def test_card_short_str_cpu_owner(self, sample_card):
        """Test the short string representation with CPU owner."""
        sample_card.owner = "CPU"
        result = sample_card.short_str()
        assert "□" in result  # CPU symbol
        assert "Geezard" in result

    def test_card_values_str(self, sample_card):
        """Test the values string representation."""
        result = sample_card.values_str()
        assert "1" in result
        assert "4" in result

    def test_card_owner_assignment(self, sample_card):
        """Test that owner can be assigned."""
        sample_card.owner = "P"
        assert sample_card.owner == "P"
        sample_card.owner = "CPU"
        assert sample_card.owner == "CPU"

    def test_all_cards_exist(self):
        """Test that all cards in CARDS dictionary can be instantiated."""
        for name in CARDS:
            card = Card(name)
            assert card.name == name
            stats = CARDS[name]
            assert card.top == stats.top
            assert card.right == stats.right
            assert card.bottom == stats.bottom
            assert card.left == stats.left
            assert card.element == stats.element
            assert card.level == stats.level

    def test_card_levels(self):
        """Test that cards have valid levels (1-9)."""
        for name in CARDS:
            card = Card(name)
            assert 1 <= card.level <= 9

    def test_card_values(self):
        """Test that card values are valid (1-10)."""
        for name in CARDS:
            card = Card(name)
            assert 1 <= card.top <= 10
            assert 1 <= card.right <= 10
            assert 1 <= card.bottom <= 10
            assert 1 <= card.left <= 10
