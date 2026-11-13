from enum import StrEnum


class TileKind(StrEnum):
    LAND = "land"
    WATER = "water"


class PlayerColor(StrEnum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    ORANGE = "orange"
    TURQUOISE = "turquoise"
    PURPLE = "purple"
    WHITE = "white"
