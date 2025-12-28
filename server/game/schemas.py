from pydantic import BaseModel

from game.enums import PlayerColor
from game.models import Tile


class JoinData(BaseModel):
    name: str
    color: PlayerColor


class AttackData(BaseModel):
    x: int
    y: int


class TileUpdateData(BaseModel):
    x: int
    y: int
    tile: Tile
