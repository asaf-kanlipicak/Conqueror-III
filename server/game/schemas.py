from pydantic import BaseModel, ConfigDict

from game.constants import BOARD_SIZE
from game.enums import BuildingKind, PlayerColor
from game.models import Coord


class Data(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JoinData(Data):
    name: str
    color: PlayerColor


class StartData(Data):
    size: int = BOARD_SIZE


class MoveData(Data):
    source: Coord
    target: Coord
    repeat: bool | None = None


class SplitData(Data):
    source: Coord
    targets: list[Coord]


class CancelData(Data):
    source: Coord
    at: Coord | None = None


class StandData(Data):
    source: Coord
    standing: bool


class BuildData(Data):
    source: Coord
    building: BuildingKind


class ResumeData(Data):
    player_id: str


class KickData(Data):
    seat: str


class ChatData(Data):
    text: str


class PauseData(Data):
    paused: bool


class ErrorData(BaseModel):
    message: str
