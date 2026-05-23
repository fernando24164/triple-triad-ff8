"""Dialog content for the Queen of Cards tutorial."""

from typing import Any

SPEAKER = "♕ Queen of Cards"

STEPS: list[dict[str, Any]] = [
    {
        "lines": [
            "Welcome, dear player! I am the Queen of Cards, ruler of all things Triple Triad.",
            "I see you are new to the game. Fear not — I shall teach you everything you need to know!",
        ],
        "interactive": None,
    },
    {
        "lines": [
            "The goal of Triple Triad is simple: capture more cards than your opponent.",
            "The board is a 3×3 grid. Each player starts with 5 cards in hand.",
            "When all 9 spaces are filled, the player controlling the most cards wins!",
        ],
        "interactive": None,
    },
    {
        "lines": [
            "Every card has four directional stats: Top, Right, Bottom, and Left.",
            "Values range from 1 (weak) to 10 (strong, shown as A).",
            "Cards may also have an Element — Fire, Ice, Thunder, Earth, Wind, Water, Poison, or Holy.",
        ],
        "interactive": None,
    },
    {
        "lines": [
            "Here is what a card looks like on the board:",
            "",
            "         ▲ Top",
            "         │",
            "  ◀ Left ┼ Right ▶",
            "         │",
            "         ▼ Bottom",
            "",
            "For example: Ifrit [Fire]  ▲9  ▶8  ▼6  ◀5",
            "When two cards face off, the higher adjacent value wins!",
        ],
        "interactive": None,
    },
    {
        "lines": [
            "Players take turns placing one card from their hand onto an empty cell.",
            "Choose which card to play, then pick a position (1-9) on the grid.",
            "Try it yourself!",
        ],
        "interactive": "place_demo",
    },
    {
        "lines": [
            "When you place a card next to an opponent's card, compare the touching values.",
            "If your value is higher, you capture their card — it flips to your side!",
            "If your value is equal or lower, nothing happens (unless special rules are in play).",
        ],
        "interactive": None,
    },
    {
        "lines": [
            "Now I will show you a capture in action. I have placed a weak card on the board.",
            "Place your stronger card next to it and watch what happens!",
        ],
        "interactive": "capture_demo",
    },
    {
        "lines": [
            "Some board cells have elemental symbols on them.",
            "If you place a card whose element matches the cell, all its sides get +1 during comparisons!",
            "This can turn a losing match-up into a winning one.",
        ],
        "interactive": "element_demo",
    },
    {
        "lines": [
            "There are a few optional rules you may encounter:",
            "  Same — If your placed card matches values on 2+ sides, capture ALL adjacent cards.",
            "  Plus — If the sums of your card + adjacent cards are equal on 2+ sides, capture them all.",
            "  Open — You can see the CPU's entire hand.",
            "  Random — Cards are dealt randomly from the full pool of 110+ cards.",
        ],
        "interactive": None,
    },
    {
        "lines": [
            "You have learned all the basics! The rest is up to you and your strategy.",
            "Positioning, elements, and clever predictions make a true Triple Triad champion.",
            "Now go forth, play, and may the cards favor you!",
        ],
        "interactive": None,
    },
]
