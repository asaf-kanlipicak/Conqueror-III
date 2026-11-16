import asyncio
from enum import StrEnum

from pydantic import BaseModel, SerializeAsAny

from connection.manager import Manager
from game.constants import BOT_PAUSE, RECONNECT_GRACE
from game.schemas import (
    BuildData,
    CancelData,
    ChatData,
    ErrorData,
    JoinData,
    KickData,
    MoveData,
    ResumeData,
    StartData,
)
from game.state import State, StateError


class CommandType(StrEnum):
    JOIN = "JOIN"
    RESUME = "RESUME"
    START = "START"
    MAP = "MAP"
    MOVE = "MOVE"
    CANCEL = "CANCEL"
    BUILD = "BUILD"
    CHAT = "CHAT"
    END_TURN = "END_TURN"
    BOT = "BOT"
    KICK = "KICK"
    RESET = "RESET"


class EventType(StrEnum):
    GAME_UPDATE = "GAME_UPDATE"


class ResultType(StrEnum):
    CONNECT_SUCCESS = "CONNECT_SUCCESS"
    JOIN_SUCCESS = "JOIN_SUCCESS"
    ERROR = "ERROR"


class Command(BaseModel):
    type: CommandType
    data: (
        JoinData
        | MoveData
        | CancelData
        | BuildData
        | ResumeData
        | ChatData
        | StartData
        | KickData
        | None
    ) = None


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
        self.bots: asyncio.Task | None = None
        self.handlers = {
            CommandType.JOIN: self.dispatch_join,
            CommandType.RESUME: self.dispatch_resume,
            CommandType.START: self.dispatch_start,
            CommandType.MAP: self.dispatch_map,
            CommandType.MOVE: self.dispatch_move,
            CommandType.CANCEL: self.dispatch_cancel,
            CommandType.BUILD: self.dispatch_build,
            CommandType.CHAT: self.dispatch_chat,
            CommandType.END_TURN: self.dispatch_end_turn,
            CommandType.BOT: self.dispatch_bot,
            CommandType.KICK: self.dispatch_kick,
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

    async def dispatch_start(self, player_id: str | None, command: Command) -> None:
        data = command.data if isinstance(command.data, StartData) else StartData()
        self.state.start(player_id, data.size)
        await self._broadcast_game()
        self._start_bots()

    async def dispatch_map(self, player_id: str | None, command: Command) -> None:
        if not isinstance(command.data, StartData):
            raise StateError("a size is required")
        self.state.shape(player_id, command.data.size)
        await self._broadcast_game()

    async def dispatch_move(self, player_id: str | None, command: Command) -> None:
        if not isinstance(command.data, MoveData):
            raise StateError("a source and a target are required")
        self.state.add_order(
            self._require_player(player_id),
            command.data.source,
            command.data.target,
            command.data.repeat,
        )
        await self._broadcast_game()

    async def dispatch_cancel(self, player_id: str | None, command: Command) -> None:
        if not isinstance(command.data, CancelData):
            raise StateError("a source is required")
        self.state.remove_order(self._require_player(player_id), command.data.source)
        await self._broadcast_game()

    async def dispatch_build(self, player_id: str | None, command: Command) -> None:
        if not isinstance(command.data, BuildData):
            raise StateError("a tile and a building are required")
        self.state.build(
            self._require_player(player_id), command.data.source, command.data.building
        )
        await self._broadcast_game()

    async def dispatch_chat(self, player_id: str | None, command: Command) -> None:
        if not isinstance(command.data, ChatData):
            raise StateError("a message is required")
        self.state.chat(self._require_player(player_id), command.data.text)
        await self._broadcast_game()

    async def dispatch_end_turn(self, player_id: str | None, _: Command) -> None:
        self.state.end_turn(self._require_player(player_id))
        await self._broadcast_game()
        self._start_bots()

    async def dispatch_bot(self, _: str | None, __: Command) -> None:
        self.state.add_bot()
        await self._broadcast_game()

    async def dispatch_kick(self, _: str | None, command: Command) -> None:
        if not isinstance(command.data, KickData):
            raise StateError("a seat is required")
        self.state.kick(command.data.seat)
        await self._broadcast_game()

    async def dispatch_reset(self, _: str | None, __: Command) -> None:
        self._stop_bots()
        self.state = State()
        await self._broadcast_game()

    async def player_left(self, player_id: str) -> None:
        if not self.state.away(player_id):
            return
        await self._broadcast_game()
        await asyncio.sleep(RECONNECT_GRACE)
        if self.state.is_online(player_id):
            return
        self.state.drop(player_id)
        await self._broadcast_game()
        self._start_bots()

    def _start_bots(self) -> None:
        if self.bots is not None and not self.bots.done():
            return
        if not any(player.bot for player in self.state.game.players):
            return
        self.bots = asyncio.create_task(self._play_bots())

    def _stop_bots(self) -> None:
        if self.bots is None:
            return
        self.bots.cancel()
        self.bots = None

    async def _play_bots(self) -> None:
        state = self.state
        while state is self.state:
            state.plan_bots()
            await self._broadcast_game()
            current = state.current
            if current is None or not current.bot or state.game.winner is not None:
                return
            await asyncio.sleep(BOT_PAUSE)
            if state is not self.state or state.current is not current:
                return
            state.end_turn(current.id)

    @staticmethod
    def _require_player(player_id: str | None) -> str:
        if player_id is None:
            raise StateError("join the game first")
        return player_id

    async def _broadcast_game(self) -> None:
        event = Event(type=EventType.GAME_UPDATE, data=self.state.game)
        await self.manager.broadcast(event)
