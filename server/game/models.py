from pydantic import BaseModel, Field

from game.enums import PlayerColor, TileKind


class Player(BaseModel):
    id: str
    name: str = Field(..., max_length=20)
    color: PlayerColor
    eliminated: bool = False
    online: bool = True


class Tile(BaseModel):
    kind: TileKind = TileKind.LAND
    owner: str | None = None
    soldiers: int = 0


class ChatLine(BaseModel):
    name: str
    text: str


class Game(BaseModel):
    tiles: list[list[Tile]]
    players: list[Player] = []
    turn: int = 0
    round: int = 0
    started: bool = False
    winner: str | None = None
    log: list[str] = []
    chat: list[ChatLine] = []
