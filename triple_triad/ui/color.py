from ..models.player import Player


class Color:
    """ANSI color codes for terminal rendering."""

    RESET = "\033[0m"
    P_FG = "\033[92m"
    CPU_FG = "\033[91m"
    BORDER = "\033[90m"
    EMPTY_POS = "\033[33m"
    HIGHLIGHT = "\033[93m"

    @staticmethod
    def player(text: str) -> str:
        return f"{Color.P_FG}{text}{Color.RESET}"

    @staticmethod
    def cpu(text: str) -> str:
        return f"{Color.CPU_FG}{text}{Color.RESET}"

    @staticmethod
    def border(text: str) -> str:
        return f"{Color.BORDER}{text}{Color.RESET}"

    @staticmethod
    def empty(text: str) -> str:
        return f"{Color.EMPTY_POS}{text}{Color.RESET}"

    @staticmethod
    def highlight(text: str) -> str:
        return f"{Color.HIGHLIGHT}{text}{Color.RESET}"

    @staticmethod
    def card(text: str, owner: Player | None) -> str:
        """Color a string based on card owner."""
        if owner == Player.PLAYER:
            return Color.player(text)
        return Color.cpu(text)
