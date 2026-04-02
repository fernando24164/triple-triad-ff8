class Color:
    """ANSI color codes for terminal rendering."""

    RESET = "\033[0m"
    # Card ownership
    P_FG = "\033[92m"  # bright green  — player
    CPU_FG = "\033[91m"  # bright red    — CPU
    # Board structure
    BORDER = "\033[90m"  # dark grey     — grid lines
    EMPTY_POS = "\033[33m"  # yellow        — empty cell number

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
    def card(text: str, owner: str) -> str:
        """Color a string based on card owner ('P' or 'CPU')."""
        if owner == "P":
            return Color.player(text)
        return Color.cpu(text)
