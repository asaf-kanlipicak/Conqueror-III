from pydantic import BaseModel

from game.enums import PlayerColor


class Coord(BaseModel):
    x: int
    y: int


class JoinData(BaseModel):
    name: str
    color: PlayerColor


class MoveData(BaseModel):
    source: Coord
    target: Coord


class CancelData(BaseModel):
    source: Coord


class ResumeData(BaseModel):
    player_id: str


class ChatData(BaseModel):
    text: str


class ErrorData(BaseModel):
    message: str
