from enum import StrEnum
from pydantic import BaseModel, SerializeAsAny

from connection.manager import Manager
from game.models import Player
from game.schemas import JoinData, AttackData, TileUpdateData
from game.state import State


class CommandType(StrEnum):
    RESET = "RESET"
    JOIN = "JOIN"
    ATTACK = "ATTACK"

class EventType(StrEnum):
    GAME_UPDATE = "GAME_UPDATE"
    GRID_UPDATE = "GRID_UPDATE"
    PLAYERS_UPDATE = "PLAYERS_UPDATE"
    TILE_UPDATE = "TILE_UPDATE"

class ResultType(StrEnum):
    CONNECT_SUCCESS = "CONNECT_SUCCESS"
    JOIN_SUCCESS = "JOIN_SUCCESS"

class Command(BaseModel):
    type: CommandType
    data: JoinData | AttackData

class Event(BaseModel):
    type: EventType
    data: SerializeAsAny[BaseModel]

class Result(BaseModel):
    type: ResultType
    data: SerializeAsAny[BaseModel]

class Dispatcher:
    def __init__(self, manager: Manager):
        self.state = State()
        self.manager = manager
        self.command_map = {
            CommandType.RESET: self.dispatch_reset,
            CommandType.JOIN: self.dispatch_join,
            CommandType.ATTACK: self.dispatch_attack
        }

    async def dispatch_reset(self, *_):
        self.state = State()
        event = Event(type=EventType.GAME_UPDATE, data=self.state.game)
        await self.manager.broadcast(event)

    async def dispatch_join(self, _, command: Command):
        assert isinstance(command.data, JoinData)
        data = command.data
        player = Player(name=data.name, color=data.color)
        players = self.state.add_player(player)
        event = Event(type=EventType.PLAYERS_UPDATE, data=players)
        result = Result(type=ResultType.JOIN_SUCCESS, data=player)
        await self.manager.broadcast(event)
        return result

    async def dispatch_attack(self, player: Player, command: Command):
        assert isinstance(command.data, AttackData)
        assert isinstance(player, Player)
        x, y = command.data.x, command.data.y
        tile = self.state.set_tile_owner(x, y, player)
        data = TileUpdateData(x=x, y=y, tile=tile)
        event = Event(type=EventType.TILE_UPDATE, data=data)
        await self.manager.broadcast(event)

    async def dispatch_command(self, player: Player | None, command: Command):
        handler = self.command_map.get(command.type)
        return await handler(player, command)