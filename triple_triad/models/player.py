from enum import Enum, StrEnum


class Player(StrEnum):
    """Side of the board that owns a card.

    A ``StrEnum`` so existing string comparisons (``card.owner == "P"``)
    keep working while code can progressively migrate to the enum.
    """

    PLAYER = "P"
    CPU = "CPU"


class Role(StrEnum):
    """Netplay role: this client's seat in a P2P match."""

    P1 = "P1"
    P2 = "P2"


class MatchResult(Enum):
    """Outcome of a match, from the local player's perspective in
    single-player and from P1/P2 seats in netplay."""

    P1_WIN = "p1_win"
    P2_WIN = "p2_win"
    DRAW = "draw"
    QUIT = "quit"
