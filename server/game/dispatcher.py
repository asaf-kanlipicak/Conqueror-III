import asyncio
from enum import StrEnum

from pydantic import BaseModel, SerializeAsAny

from connection.manager import Manager
from game.constants import RECONNECT_GRACE
from game.schemas import CancelData, ChatData, ErrorData, JoinData, MoveData, ResumeData
from game.state import State, StateError


class CommandType(StrEnum):
    JOIN = "JOIN"
    RESUME = "RESUME"
    START = "START"
    MOVE = "MOVE"
    CANCEL = "CANCEL"
    CHAT = "CHAT"
    END_TURN = "END_TURN"
    RESET = "RESET"


class EventType(StrEnum):
    GAME_UPDATE = "GAME_UPDATE"


class ResultType(StrEnum):
    CONNECT_SUCCESS = "CONNECT_SUCCESS"
    JOIN_SUCCESS = "JOIN_SUCCESS"
    ORDER_ACCEPTED = "ORDER_ACCEPTED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    ERROR = "ERROR"


class Command(BaseModel):
    type: CommandType
    data: JoinData | MoveData | CancelData | ResumeData | ChatData | None = None


class Event(BaseModel):
    type: EventType
    data: SerializeAsAny[BaseModel]


class Result(BaseModel):
    type: ResultType
    data: SerializeAsAny[BaseModel] | None = None


class Dispatcher:
    def __init__(self, manager: Manager):
        self.state = State()
        self.manager = manager
        self.handlers = {
            CommandType.JOIN: self.dispatch_join,
            CommandType.RESUME: self.dispatch_resume,
            CommandType.START: self.dispatch_start,
            CommandType.MOVE: self.dispatch_move,
            CommandType.CANCEL: self.dispatch_cancel,
            CommandType.CHAT: self.dispatch_chat,
            CommandType.END_TURN: self.dispatch_end_turn,
            CommandType.RESET: self.dispatch_reset,
        }

    async def dispatch_command(self, player_id: str | None, command: Command) -> Result | None:
        try:
            return await self.handlers[command.type](player_id, command)
        except StateError as error:
            return Result(type=ResultType.ERROR, data=ErrorData(message=str(error)))

    async def dispatch_join(self, _: str | None, command: Command) -> Result:
        if not isinstance(command.data, JoinData):
            raise StateError("a name and a color are required")
        player = self.state.join(command.data.name, command.data.color)
        await self._broadcast_game()
        return Result(type=ResultType.JOIN_SUCCESS, data=player)

    async def dispatch_resume(self, _: str | None, command: Command) -> Result:
        if not isinstance(command.data, ResumeData):
            raise StateError("a player id is required")
        player = self.state.resume(command.data.player_id)
        await self._broadcast_game()
        return Result(type=ResultType.JOIN_SUCCESS, data=player)

    async def dispatch_start(self, player_id: str | None, _: Command) -> None:
        self.state.start(self._require_player(player_id))
        await self._broadcast_game()

    async def dispatch_move(self, player_id: str | None, command: Command) -> Result:
        if not isinstance(command.data, MoveData):
            raise StateError("a source and a target are required")
        self.state.add_order(
            self._require_player(player_id), command.data.source, command.data.target
        )
        return Result(type=ResultType.ORDER_ACCEPTED, data=command.data)

    async def dispatch_cancel(self, player_id: str | None, command: Command) -> Result:
        if not isinstance(command.data, CancelData):
            raise StateError("a source is required")
        self.state.remove_order(self._require_player(player_id), command.data.source)
        return Result(type=ResultType.ORDER_CANCELLED, data=command.data)

    async def dispatch_chat(self, player_id: str | None, command: Command) -> None:
        if not isinstance(command.data, ChatData):
            raise StateError("a message is required")
        self.state.chat(self._require_player(player_id), command.data.text)
        await self._broadcast_game()

    async def dispatch_end_turn(self, player_id: str | None, _: Command) -> None:
        self.state.end_turn(self._require_player(player_id))
        await self._broadcast_game()

    async def dispatch_reset(self, _: str | None, __: Command) -> None:
        self.state = State()
        await self._broadcast_game()

    async def player_left(self, player_id: str) -> None:
        await asyncio.sleep(RECONNECT_GRACE)
        if self.state.is_online(player_id):
            return
        self.state.disconnect(player_id)
        await self._broadcast_game()

    @staticmethod
    def _require_player(player_id: str | None) -> str:
        if player_id is None:
            raise StateError("join the game first")
        return player_id

    async def _broadcast_game(self) -> None:
        event = Event(type=EventType.GAME_UPDATE, data=self.state.game)
        await self.manager.broadcast(event)
