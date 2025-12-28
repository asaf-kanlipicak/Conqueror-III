from enum import StrEnum

class TileType(StrEnum):
    PLAYER = "player"
    BOT = "bot"

class PlayerColor(StrEnum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    ORANGE = "orange"
    TURQUOISE = "turquoise"
    PURPLE = "purple"
    WHITE = "white"

class BotColor(StrEnum):
    GREY = "grey"
    BLACK = "black"

