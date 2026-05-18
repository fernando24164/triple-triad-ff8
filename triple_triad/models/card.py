from ..data.cards import CARDS, CardStats, Element


def stat_display(value: int) -> str:
    """Convert a card stat value to display string (10 -> 'A')."""
    return "A" if value == 10 else str(value)


class Card:
    """A playing card with mutable game state (owner) and immutable stats.

    Uses __slots__ for better memory efficiency (~40% reduction per instance).
    Stats are accessed via properties from the immutable _stats reference
    instead of being duplicated as instance attributes.
    """

    __slots__ = ("name", "_stats", "owner")

    def __init__(self, name: str) -> None:
        self.name = name
        self._stats: CardStats = CARDS[name]
        self.owner: str | None = None  # 'P' or 'CPU'

    # Properties for stats - read from immutable _stats
    @property
    def top(self) -> int:
        return self._stats.top

    @property
    def right(self) -> int:
        return self._stats.right

    @property
    def bottom(self) -> int:
        return self._stats.bottom

    @property
    def left(self) -> int:
        return self._stats.left

    @property
    def element(self) -> Element | None:
        return self._stats.element

    @property
    def level(self) -> int:
        return self._stats.level

    def __str__(self) -> str:
        el = f"[{self.element.value}]" if self.element else ""
        return (
            f"{self.name}{el} "
            f"T:{stat_display(self.top)} R:{stat_display(self.right)} "
            f"B:{stat_display(self.bottom)} L:{stat_display(self.left)} "
            f"Lv:{self.level}"
        )

    def short_str(self, width: int = 18) -> str:
        """Short display for board rendering."""
        owner_sym = "■" if self.owner == "P" else "□"
        name_trunc = self.name[: width - 2]
        return f"{owner_sym}{name_trunc}"

    def values_str(self) -> str:
        return (
            f"  {stat_display(self.top)}  \n"
            f"{stat_display(self.left)}   {stat_display(self.right)}\n"
            f"  {stat_display(self.bottom)}  "
        )

    def __repr__(self) -> str:
        return (
            f"Card(name={self.name!r}, top={self.top}, right={self.right}, "
            f"bottom={self.bottom}, left={self.left}, element={self.element}, "
            f"level={self.level}, owner={self.owner})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.name == other.name and self.owner == other.owner

    def __hash__(self) -> int:
        return hash((self.name, self.owner))
