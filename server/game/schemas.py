from pydantic import BaseModel

from game.constants import BOARD_SIZE
from game.enums import PlayerColor
from game.models import Coord


class JoinData(BaseModel):
    name: str
    color: PlayerColor


class StartData(BaseModel):
    size: int = BOARD_SIZE


class MoveData(BaseModel):
    source: Coord
    target: Coord
    repeat: bool | None = None


class CancelData(BaseModel):
    source: Coord


class ResumeData(BaseModel):
    player_id: str


class ChatData(BaseModel):
    text: str


class ErrorData(BaseModel):
    message: str
