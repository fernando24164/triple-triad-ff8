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
            "For example: Ifrit [Fire]  ▲9  ▶6  ▼2  ◀8",
            "When two cards face off, the higher adjacent value wins!",
        ],
        "interactive": None,
    },
    {
        "lines": [
            "Players take turns placing one card from their hand onto an empty cell.",
            "Choose which card to play, then use the arrow keys to highlight an empty cell.",
            "Press Enter to place your card. Try it yourself!",
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
            "A mismatched (or elementless) card on that cell gets -1 instead — even the opponent's cards!",
            "This can turn a losing match-up into a winning one.",
        ],
        "interactive": "element_demo",
    },
    {
        "lines": [
            "There are a few optional rules you may encounter:",
            "  Same — If your placed card matches values on 2+ sides, capture ALL adjacent cards.",
            "  Same Wall — Board edges count as a rank A side for the Same rule.",
            "  Plus — If the sums of your card + adjacent cards are equal on 2+ sides, capture them all.",
            "  Combo — Cards flipped by Same/Plus chain-capture their own neighbors automatically.",
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

RULE_TOPIC_STEPS: dict[str, dict[str, Any]] = {
    "capture": {
        "lines": [
            "How Capture Works",
            "",
            "When two cards are adjacent, the touching values are compared:",
            "",
            "  Your Right  vs  Opponent's Left",
            "  Your Left   vs  Opponent's Right",
            "  Your Top    vs  Opponent's Bottom",
            "  Your Bottom vs  Opponent's Top",
            "",
            "If your value is higher, you capture their card!",
            "If equal or lower, nothing happens (unless Same or Plus is active).",
            "",
            "Elements can change the outcome — a matching cell gives +1 to ALL",
            "your sides, while a mismatched cell penalizes everyone.",
        ],
        "interactive": "capture_demo",
    },
    "elements": {
        "lines": [
            "Element Squares",
            "",
            "Some board cells have elemental symbols on them.",
            "",
            "If your card's element matches the cell:",
            "  → All four sides get +1 during comparisons",
            "",
            "If you place a card with mismatching (or no) element:",
            "  → ALL sides on that cell get -1 (yours AND the opponent's)",
            "",
            "This means element squares let you turn a losing match-up",
            "into a winning one — or vice-versa if you're unprepared!",
        ],
        "interactive": "element_demo",
    },
    "same": {
        "lines": [
            "The Same Rule",
            "",
            "If you place a card and 2 or more of its sides match the",
            "touching opponent values exactly (equal, not higher), you",
            "capture ALL adjacent opponent cards at once!",
            "",
            "Example:",
            "  Your card  [T:3  R:4  B:5  L:3]",
            "  Opponent above  (bottom=3) → matches your Top(3)",
            "  Opponent left    (right=3) → matches your Left(3)",
            "",
            "2 matching sides → Same triggers — capture both!",
        ],
        "interactive": "same_demo",
    },
    "same_wall": {
        "lines": [
            "Same Wall",
            "",
            "When Same is active, the board edges count as a rank A (10)",
            "side for the 2+ match requirement — but a wall has no card",
            "to capture, so it only helps trigger the rule.",
            "",
            "Example on a corner cell:",
            "  Your card  [T:10  R:2  B:8  L:6]",
            "  Top wall   counts as 10 → matches your Top(10)",
            "  1 real match + 1 wall = 2 → Same triggers!",
            "",
            "This is especially powerful on corner and edge cells!",
        ],
        "interactive": "same_wall_demo",
    },
    "plus": {
        "lines": [
            "The Plus Rule",
            "",
            "If the sums of your card's values plus the adjacent opponent",
            "values are equal on 2 or more sides, you capture them all!",
            "",
            "Example:",
            "  Your card  [T:2  R:1  B:4  L:4]",
            "  Opponent above (bottom=4) → sum = 2+4 = 6",
            "  Opponent left    (right=2) → sum = 4+2 = 6",
            "",
            "Equal sums on 2 sides → Plus triggers — capture both!",
        ],
        "interactive": "plus_demo",
    },
    "combo": {
        "lines": [
            "The Combo Rule",
            "",
            "When Same or Plus triggers, every card flipped during that",
            "turn can automatically chain-capture its own neighbors",
            "using the basic (higher-value-wins) rule.",
            "",
            "This chain reaction is the Combo rule — it can turn a single",
            "placement into a board-wide wipeout!",
            "",
            "Note: Same and Plus are NOT re-evaluated during the chain,",
            "only the basic comparison is used for each step.",
        ],
        "interactive": "combo_demo",
    },
}
