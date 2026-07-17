import random
import time
from dataclasses import dataclass

from blessed import Terminal

term = Terminal()

FRAME_W = 62
BOX_W = 34

ROUND_LABELS = ["ROUND 1", "ROUND 2", "FINAL"]

RIVALS = [
    "Zell Dincht",
    "Selphie Tilmitt",
    "Irvine Kinneas",
    "Quistis Trepe",
    "Xu",
    "Raijin",
    "Fujin",
    "Nida",
]

BOSSES = [
    "Seifer Almasy",
    "Edea Kramer",
    "NORG",
    "Queen of the Cards"
]


@dataclass
class BracketMatch:
    round_num: int
    label: str
    opponent: str
    result: str | None = None  # "W", "L", or "D"


def build_bracket() -> list[BracketMatch]:
    """Pick 3 unique FF8 opponents (2 rivals + 1 boss) for the tournament ladder."""
    rivals = random.sample(RIVALS, 2)
    boss = random.choice(BOSSES)
    opponents = [*rivals, boss]
    return [
        BracketMatch(round_num=i + 1, label=ROUND_LABELS[i], opponent=opponents[i])
        for i in range(3)
    ]


def _center(text: str, width: int = FRAME_W) -> str:
    return term.center(text, width)


def _dim(text: str) -> str:
    # "dim" isn't a compoundable style in blessed — apply it as a raw
    # escape/reset pair instead of calling it like term.bold(text).
    return f"{term.dim}{text}{term.normal}"


def _status_text(match: BracketMatch, is_current: bool) -> str:
    if match.result == "W":
        return term.bold_green("✓ DEFEATED")
    if match.result == "L":
        return term.bold_red("✗ LOST")
    if match.result == "D":
        return term.bold_yellow("➗ DRAW")
    if is_current:
        return term.bold_yellow("⚔ IN PROGRESS")
    return _dim("⏳ pending")


def _box(title: str, subtitle: str, status: str) -> list[str]:
    inner = BOX_W - 2
    top = "┌" + "─" * inner + "┐"
    bottom = "└" + "─" * inner + "┘"
    return [
        top,
        "│" + term.center(title, inner) + "│",
        "│" + term.center(subtitle, inner) + "│",
        "│" + term.center(status, inner) + "│",
        bottom,
    ]


def render_tree(
    matches: list[BracketMatch],
    current_round: int | None = None,
    revealed: int = 3,
    champion: bool = False,
) -> list[str]:
    """Render the tournament ladder from CHAMPION (top) down to YOU (bottom)."""
    trophy = "🏆  C H A M P I O N  🏆"
    lines = [
        _center(term.bold_yellow(trophy) if champion else _dim(trophy)),
        _center("│"),
    ]

    for match in reversed(matches):
        name = match.opponent if revealed >= match.round_num else _dim("???")
        is_current = current_round == match.round_num
        status = _status_text(match, is_current)
        for row in _box(match.label, name, status):
            lines.append(_center(row))
        lines.append(_center("│"))

    lines.append(_center(term.bold("YOU")))
    return lines


def _draw(lines: list[str]) -> None:
    print(term.clear)
    print("\n".join(lines))


def show_bracket_reveal(matches: list[BracketMatch]) -> None:
    """Reveal each opponent bottom-to-top before the tournament begins."""
    for revealed in range(len(matches) + 1):
        _draw(render_tree(matches, revealed=revealed))
        time.sleep(0.45)
    time.sleep(0.5)


def show_round_intro(matches: list[BracketMatch], round_index: int) -> None:
    """Highlight the upcoming match with a blink, then announce the opponent."""
    match = matches[round_index]
    for i in range(4):
        highlight = match.round_num if i % 2 == 0 else None
        _draw(render_tree(matches, current_round=highlight))
        time.sleep(0.18)
    _draw(render_tree(matches, current_round=match.round_num))
    print()
    print(term.bold_yellow(_center(f"⚔  VS {match.opponent}  ⚔")))
    print()


def show_round_result(
    matches: list[BracketMatch], round_index: int, result: str
) -> None:
    """Mark the round's result on the tree and animate advancement on a win."""
    match = matches[round_index]
    match.result = result
    for i in range(3):
        highlight = match.round_num if i % 2 == 0 else None
        _draw(render_tree(matches, current_round=highlight))
        time.sleep(0.15)
    _draw(render_tree(matches))

    if result == "W" and round_index < len(matches) - 1:
        for i in range(4):
            _draw(render_tree(matches))
            if i % 2 == 0:
                print(term.bold_green(_center("▲ Advancing to the next round...")))
            time.sleep(0.25)
    time.sleep(0.6)


def show_champion_finale(matches: list[BracketMatch]) -> None:
    """Final animation: light up the trophy if every round was won."""
    won_all = all(m.result == "W" for m in matches)
    for i in range(4):
        _draw(render_tree(matches, champion=won_all and i % 2 == 0))
        time.sleep(0.3)
    _draw(render_tree(matches, champion=won_all))
