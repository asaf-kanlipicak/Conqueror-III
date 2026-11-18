from pydantic import BaseModel, Field

from game.constants import BOARD_SIZE
from game.enums import BuildingKind, PlayerColor, TileKind


class Coord(BaseModel):
    x: int
    y: int


class Player(BaseModel):
    id: str
    name: str = Field(..., max_length=20)
    color: PlayerColor
    eliminated: bool = False
    online: bool = True
    bot: bool = False
    gold: int = 0
    capital: Coord | None = None
    capital_lost: int = 0


class Tile(BaseModel):
    kind: TileKind = TileKind.LAND
    owner: str | None = None
    soldiers: int = 0
    loot: int = 0
    buildings: list[BuildingKind] = []


class PendingOrder(BaseModel):
    player: str
    source: Coord
    target: Coord
    soldiers: int
    repeat: bool = False
    parts: int = 1


class ChatLine(BaseModel):
    name: str
    text: str
    at: float


class Game(BaseModel):
    size: int = BOARD_SIZE
    tiles: list[list[Tile]]
    players: list[Player] = []
    orders: list[PendingOrder] = []
    turn: int = 0
    round: int = 0
    started: bool = False
    paused: bool = False
    started_at: float | None = None
    winner: str | None = None
    log: list[str] = []
    chat: list[ChatLine] = []
