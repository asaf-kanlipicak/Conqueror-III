import random
import uuid
from dataclasses import dataclass
from math import ceil

from game.constants import (
    BOARD_SIZE,
    CAPITAL_GARRISON,
    CHAT_LIMIT,
    CHAT_MAX,
    LOG_LIMIT,
    LOOT,
    NEUTRAL_GARRISONS,
    PRODUCTION,
    RIVER_START,
    RIVER_WIDTH,
    SEATS,
)
from game.enums import PlayerColor, TileKind
from game.models import ChatLine, Game, Player, Tile
from game.schemas import Coord


class StateError(Exception):
    pass


@dataclass
class Order:
    source: Coord
    target: Coord
    soldiers: int


def _is_water(x: int, y: int) -> bool:
    across = RIVER_START <= x < RIVER_START + RIVER_WIDTH
    down = RIVER_START <= y < RIVER_START + RIVER_WIDTH
    return across or down


def _label(coord: Coord) -> str:
    return f"({coord.x}, {coord.y})"


class State:
    def __init__(self):
        self.game = Game(tiles=self._build_tiles())
        self.orders: list[Order] = []

    @staticmethod
    def _build_tiles() -> list[list[Tile]]:
        rows = []
        for y in range(BOARD_SIZE):
            row = []
            for x in range(BOARD_SIZE):
                if _is_water(x, y):
                    row.append(Tile(kind=TileKind.WATER))
                else:
                    row.append(Tile(soldiers=random.choice(NEUTRAL_GARRISONS)))
            rows.append(row)
        return rows

    @property
    def current(self) -> Player | None:
        if not self.game.started:
            return None
        return self.game.players[self.game.turn]

    def tile(self, coord: Coord) -> Tile:
        return self.game.tiles[coord.y][coord.x]

    def player(self, player_id: str) -> Player:
        player = self._find(player_id)
        if player is None:
            raise StateError("you are not in this game")
        return player

    def _find(self, player_id: str) -> Player | None:
        for player in self.game.players:
            if player.id == player_id:
                return player
        return None

    def join(self, name: str, color: PlayerColor) -> Player:
        name = name.strip()
        if not name:
            raise StateError("a name is required")
        if self.game.started:
            raise StateError("the game has already started")
        if len(self.game.players) >= len(SEATS):
            raise StateError("the game is full")
        if any(player.name == name for player in self.game.players):
            raise StateError("that name is taken")
        if any(player.color == color for player in self.game.players):
            raise StateError("that color is taken")
        player = Player(id=uuid.uuid4().hex[:8], name=name, color=color)
        self.game.players.append(player)
        self._log(f"{player.name} joined as {player.color}")
        return player

    def resume(self, player_id: str) -> Player:
        player = self.player(player_id)
        player.online = True
        self._log(f"{player.name} is back")
        current = self.current
        if self.game.winner is None and current is not None and not current.online:
            self._next_turn()
        return player

    def disconnect(self, player_id: str) -> None:
        player = self._find(player_id)
        if player is None or not player.online:
            return
        player.online = False
        current = self.current
        if self.game.winner is not None or current is None or current.id != player.id:
            self._log(f"{player.name} dropped out")
            return
        self.orders = []
        self._log(f"{player.name} dropped out, turn skipped")
        self._next_turn()

    def is_online(self, player_id: str) -> bool:
        player = self._find(player_id)
        return player is not None and player.online

    def start(self, player_id: str) -> None:
        self.player(player_id)
        if self.game.started:
            raise StateError("the game has already started")
        if len(self.game.players) < 2:
            raise StateError("at least two players are needed")
        for player, (x, y) in zip(self.game.players, SEATS):
            tile = self.game.tiles[y][x]
            tile.owner = player.id
            tile.soldiers = CAPITAL_GARRISON
        self.game.started = True
        self.game.round = 1
        self._log(f"the game is on with {len(self.game.players)} players")
        self._produce()
        current = self.current
        if current is not None and not current.online:
            self._next_turn()

    def add_order(self, player_id: str, source: Coord, target: Coord) -> None:
        player = self._require_turn(player_id)
        tile = self.tile(source)
        if tile.owner != player.id:
            raise StateError("you do not own that tile")
        if tile.soldiers == 0:
            raise StateError("that tile has no soldiers")
        if abs(source.x - target.x) + abs(source.y - target.y) != 1:
            raise StateError("those tiles are not adjacent")
        if any(order.source == source for order in self.orders):
            raise StateError("that tile already has an order")
        self.orders.append(Order(source=source, target=target, soldiers=tile.soldiers))

    def remove_order(self, player_id: str, source: Coord) -> None:
        self._require_turn(player_id)
        for order in self.orders:
            if order.source == source:
                self.orders.remove(order)
                return
        raise StateError("that tile has no order")

    def chat(self, player_id: str, text: str) -> None:
        player = self.player(player_id)
        text = " ".join(text.split())[:CHAT_MAX]
        if not text:
            raise StateError("say something first")
        self.game.chat.append(ChatLine(name=player.name, text=text))
        del self.game.chat[:-CHAT_LIMIT]

    def end_turn(self, player_id: str) -> None:
        player = self._require_turn(player_id)
        for order in list(self.orders):
            self._resolve(player, order)
        self.orders = []
        self._eliminate()
        if self._finish():
            return
        self._next_turn()

    def _require_turn(self, player_id: str) -> Player:
        player = self.player(player_id)
        current = self.current
        if current is None or current.id != player.id:
            raise StateError("it is not your turn")
        return player

    def _resolve(self, player: Player, order: Order) -> None:
        source = self.tile(order.source)
        target = self.tile(order.target)
        count = min(order.soldiers, source.soldiers)
        if source.owner != player.id or count == 0:
            self._log(f"{player.name}: nothing left at {_label(order.source)}")
            return
        if target.owner == player.id:
            target.soldiers += count
            source.soldiers -= count
            self._log(f"{player.name} moved {count} to {_label(order.target)}")
            return
        if target.soldiers == 0:
            target.owner = player.id
            target.soldiers = count
            source.soldiers -= count
            self._log(f"{player.name} walked into {_label(order.target)} with {count}")
            return
        self._battle(player, source, target, count, _label(order.target))

    def _battle(self, player: Player, source: Tile, target: Tile, attacker: int, where: str) -> None:
        defender = target.soldiers
        total = attacker + defender
        if random.random() < attacker / total:
            survivors = max(attacker - attacker * defender // (2 * total), 1)
            remaining = defender - min(attacker, defender)
            if remaining:
                target.soldiers = remaining
                source.soldiers -= attacker - survivors
                self._log(
                    f"{player.name} attacked {where} {attacker} vs {defender}: won the exchange, "
                    f"{remaining} defenders hold, attacker down to {survivors}"
                )
                return
            loot = LOOT if target.kind == TileKind.LAND and target.owner is None else 0
            target.owner = player.id
            target.soldiers = survivors + loot
            source.soldiers -= attacker
            line = f"{player.name} took {where} {attacker} vs {defender}: {survivors} soldiers"
            self._log(line + (f" and looted {loot}" if loot else ""))
            return
        source.soldiers -= ceil(attacker * defender / total)
        target.soldiers = defender - attacker * defender // (2 * total)
        self._log(
            f"{player.name} attacked {where} {attacker} vs {defender}: repelled, "
            f"attacker down to {source.soldiers}, defenders down to {target.soldiers}"
        )

    def _eliminate(self) -> None:
        for player in self.game.players:
            if player.eliminated or self._owns_land(player.id):
                continue
            player.eliminated = True
            self._log(f"{player.name} is out")
            for row in self.game.tiles:
                for tile in row:
                    if tile.owner == player.id:
                        tile.owner = None
                        tile.soldiers = 0

    def _owns_land(self, player_id: str) -> bool:
        return any(
            tile.owner == player_id and tile.kind == TileKind.LAND
            for row in self.game.tiles
            for tile in row
        )

    def _finish(self) -> bool:
        alive = [player for player in self.game.players if not player.eliminated]
        if len(alive) != 1:
            return False
        self.game.winner = alive[0].id
        self._log(f"{alive[0].name} wins")
        return True

    def _next_turn(self) -> None:
        count = len(self.game.players)
        skipped = []
        for offset in range(1, count + 1):
            index = (self.game.turn + offset) % count
            player = self.game.players[index]
            if player.eliminated:
                continue
            if not player.online:
                skipped.append(player.name)
                continue
            if index <= self.game.turn:
                self.game.round += 1
                self._produce()
            self.game.turn = index
            for name in skipped:
                self._log(f"{name}'s turn skipped, offline")
            return

    def _produce(self) -> None:
        for row in self.game.tiles:
            for tile in row:
                if tile.kind == TileKind.LAND and tile.owner is not None:
                    tile.soldiers += PRODUCTION

    def _log(self, line: str) -> None:
        self.game.log.append(line)
        del self.game.log[:-LOG_LIMIT]
