import random
import time
import uuid
from math import ceil

from game import bot
from game.constants import (
    BOARD_SIZE,
    BOARD_SIZES,
    BOT_NAMES,
    BUILDING_COST,
    CAPITAL_GARRISON,
    CHAT_LIMIT,
    CHAT_MAX,
    FARM_BONUS,
    FORT_DEFENSE,
    GOLD_PER_BOT,
    LOG_LIMIT,
    NEUTRAL_MAX,
    NEUTRAL_MIN,
    NEUTRAL_SPREAD,
    PRODUCTION,
    RIVER_WIDTH,
)
from game.enums import BuildingKind, PlayerColor, TileKind
from game.models import ChatLine, Coord, Game, PendingOrder, Player, Tile


class StateError(Exception):
    pass


def _river(size: int) -> tuple[int, int]:
    return (size - RIVER_WIDTH) // 2, RIVER_WIDTH


def _ring(x: int, y: int, size: int) -> int:
    edge = size - 1
    return max(min(x, edge - x), min(y, edge - y))


def _garrison(ring: int, top: int) -> int:
    share = max(0, ring - 1) / max(1, top - 2)
    base = NEUTRAL_MIN + (NEUTRAL_MAX - NEUTRAL_MIN) * share
    spread = base * NEUTRAL_SPREAD
    return round(random.uniform(base - spread, base + spread))


def _seats(size: int) -> tuple[tuple[int, int], ...]:
    edge = size - 1
    return (0, 0), (edge, edge), (edge, 0), (0, edge)


def _label(coord: Coord) -> str:
    return f"({coord.x}, {coord.y})"


def _settle(tile: Tile) -> None:
    if tile.soldiers > 0:
        return
    tile.soldiers = 0
    if tile.kind == TileKind.WATER:
        tile.owner = None


def _raze(tile: Tile) -> str:
    if not tile.buildings:
        return ""
    razed = " and ".join(f"a {building}" for building in tile.buildings)
    tile.buildings = []
    return f", razed {razed}"


class State:
    def __init__(self):
        self.game = Game(tiles=self._build_tiles(BOARD_SIZE))

    @staticmethod
    def _build_tiles(size: int) -> list[list[Tile]]:
        start, width = _river(size)
        rows = []
        for y in range(size):
            row = []
            for x in range(size):
                wet = start <= x < start + width or start <= y < start + width
                if wet:
                    row.append(Tile(kind=TileKind.WATER))
                else:
                    garrison = _garrison(_ring(x, y, size), start)
                    row.append(Tile(soldiers=garrison, loot=garrison // 2))
            rows.append(row)
        return rows

    @property
    def current(self) -> Player | None:
        if not self.game.started:
            return None
        return self.game.players[self.game.turn]

    def tile(self, coord: Coord) -> Tile:
        if not (0 <= coord.x < self.game.size and 0 <= coord.y < self.game.size):
            raise StateError("that tile is off the board")
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
        if len(self.game.players) >= len(_seats(BOARD_SIZE)):
            raise StateError("the game is full")
        if any(player.name == name for player in self.game.players):
            raise StateError("that name is taken")
        if any(player.color == color for player in self.game.players):
            raise StateError("that color is taken")
        player = Player(id=uuid.uuid4().hex[:8], name=name, color=color)
        self.game.players.append(player)
        self._log(f"{player.name} joined as {player.color}")
        return player

    def add_bot(self) -> Player:
        if self.game.started:
            raise StateError("the game has already started")
        if len(self.game.players) >= len(_seats(BOARD_SIZE)):
            raise StateError("the game is full")
        taken = {player.color for player in self.game.players}
        color = next(color for color in PlayerColor if color not in taken)
        names = {player.name for player in self.game.players}
        name = random.choice([name for name in BOT_NAMES if name not in names])
        player = Player(id=uuid.uuid4().hex[:8], name=name, color=color, bot=True)
        self.game.players.append(player)
        self._log(f"{player.name} joined as {player.color}")
        return player

    def resume(self, player_id: str) -> Player:
        player = self.player(player_id)
        player.online = True
        self._log(f"{player.name} is back")
        return player

    def away(self, player_id: str) -> bool:
        player = self._find(player_id)
        if player is None or not player.online:
            return False
        player.online = False
        return True

    def drop(self, player_id: str) -> None:
        player = self._find(player_id)
        if player is None or player.online:
            return
        self.game.orders = [order for order in self.game.orders if order.player != player.id]
        current = self.current
        if self.game.winner is not None or current is None or current.id != player.id:
            self._log(f"{player.name} dropped out")
            return
        self._log(f"{player.name} dropped out, turn skipped")
        self._next_turn()

    def is_online(self, player_id: str) -> bool:
        player = self._find(player_id)
        return player is not None and player.online

    def shape(self, player_id: str | None, size: int) -> None:
        if player_id is not None:
            self.player(player_id)
        if self.game.started:
            raise StateError("the map is already in play")
        if size not in BOARD_SIZES:
            raise StateError("that board is not on offer")
        self.game.size = size
        self.game.tiles = self._build_tiles(size)

    def start(self, player_id: str | None, size: int = BOARD_SIZE) -> None:
        if player_id is not None:
            self.player(player_id)
        if self.game.started:
            raise StateError("the game has already started")
        if len(self.game.players) < 2:
            raise StateError("at least two players are needed")
        if size not in BOARD_SIZES:
            raise StateError("that board is not on offer")
        if size != self.game.size:
            self.game.size = size
            self.game.tiles = self._build_tiles(size)
        self.game.orders = []
        for player, (x, y) in zip(self.game.players, _seats(size)):
            tile = self.game.tiles[y][x]
            tile.owner = player.id
            tile.soldiers = CAPITAL_GARRISON
        self.game.started = True
        self.game.started_at = time.time()
        self.game.round = 1
        self._log(f"the game is on, {len(self.game.players)} players on a {size} by {size} board")
        self._produce()
        current = self.current
        if current is not None and not current.online:
            self._next_turn()

    def add_order(
        self, player_id: str, source: Coord, target: Coord, repeat: bool | None = None
    ) -> None:
        player = self._playing(player_id)
        tile = self.tile(source)
        if tile.owner != player.id:
            raise StateError("you do not own that tile")
        if tile.soldiers == 0:
            raise StateError("that tile has no soldiers")
        if abs(source.x - target.x) + abs(source.y - target.y) != 1:
            raise StateError("those tiles are not adjacent")
        self.tile(target)
        previous = next((order for order in self.game.orders if order.source == source), None)
        if repeat is None:
            repeat = previous.repeat if previous else False
        self.game.orders = [order for order in self.game.orders if order.source != source]
        self.game.orders.append(
            PendingOrder(
                player=player.id,
                source=source,
                target=target,
                soldiers=tile.soldiers,
                repeat=repeat,
            )
        )

    def remove_order(self, player_id: str, source: Coord) -> None:
        player = self._playing(player_id)
        for order in self.game.orders:
            if order.source == source and order.player == player.id:
                self.game.orders.remove(order)
                return
        raise StateError("that tile has no order")

    def build(self, player_id: str, coord: Coord, building: BuildingKind) -> None:
        player = self._require_turn(player_id)
        if player.eliminated:
            raise StateError("you are out of the game")
        self._raise(player, coord, building)

    def _raise(self, player: Player, coord: Coord, building: BuildingKind) -> None:
        tile = self.tile(coord)
        if tile.owner != player.id:
            raise StateError("that tile is not yours")
        if tile.kind != TileKind.LAND:
            raise StateError("nothing can be built on water")
        if building in tile.buildings:
            raise StateError(f"there is already a {building} there")
        if player.gold < BUILDING_COST:
            raise StateError(f"a {building} costs {BUILDING_COST} gold")
        player.gold -= BUILDING_COST
        tile.buildings.append(building)
        self._log(f"{player.name} raised a {building} at {_label(coord)}")

    def plan_bots(self) -> None:
        if not self.game.started or self.game.winner is not None:
            return
        current = self.current
        for player in self.game.players:
            if not player.bot or player.eliminated:
                continue
            self.game.orders = [order for order in self.game.orders if order.player != player.id]
            plan = bot.think(self.game, player)
            for order in plan.orders:
                self.add_order(player.id, order.source, order.target)
            if current is not None and current.id == player.id:
                for coord, building in plan.builds:
                    self._raise(player, coord, building)

    def chat(self, player_id: str, text: str) -> None:
        player = self.player(player_id)
        text = " ".join(text.split())[:CHAT_MAX]
        if not text:
            raise StateError("say something first")
        self.game.chat.append(ChatLine(name=player.name, text=text, at=time.time()))
        del self.game.chat[:-CHAT_LIMIT]

    def end_turn(self, player_id: str) -> None:
        player = self._require_turn(player_id)
        for order in self.game.orders:
            if order.player != player.id or not order.repeat:
                continue
            source = self.tile(order.source)
            if source.owner == player.id:
                order.soldiers = source.soldiers
        kept = []
        for order in self.game.orders:
            if order.player != player.id:
                kept.append(order)
                continue
            self._resolve(player, order)
            if order.repeat:
                kept.append(order)
        self.game.orders = kept
        self._prune_orders()
        self._eliminate()
        if self._finish():
            return
        self._next_turn()

    def _playing(self, player_id: str) -> Player:
        player = self.player(player_id)
        if not self.game.started:
            raise StateError("the game has not started")
        if player.eliminated:
            raise StateError("you are out of the game")
        return player

    def _require_turn(self, player_id: str) -> Player:
        player = self.player(player_id)
        current = self.current
        if current is None or current.id != player.id:
            raise StateError("it is not your turn")
        return player

    def _resolve(self, player: Player, order: PendingOrder) -> None:
        source = self.tile(order.source)
        target = self.tile(order.target)
        count = min(order.soldiers, source.soldiers)
        if source.owner != player.id:
            return
        if count == 0:
            self._log(f"{player.name}: nothing left at {_label(order.source)}")
            return
        if target.owner == player.id:
            target.soldiers += count
            source.soldiers -= count
            _settle(source)
            self._log(f"{player.name} moved {count} to {_label(order.target)}")
            return
        if target.soldiers == 0:
            gold = GOLD_PER_BOT if target.kind == TileKind.LAND and target.owner is None else 0
            target.owner = player.id
            target.soldiers = count
            player.gold += gold
            source.soldiers -= count
            _settle(source)
            line = f"{player.name} walked into {_label(order.target)} with {count}"
            if gold:
                line += f", seized {gold} gold"
            self._log(line + _raze(target))
            return
        self._battle(player, source, target, count, _label(order.target))

    def _battle(self, player: Player, source: Tile, target: Tile, attacker: int, where: str) -> None:
        defender = target.soldiers
        guard = defender * FORT_DEFENSE if BuildingKind.FORT in target.buildings else defender
        total = attacker + guard
        if random.random() < attacker / total:
            survivors = max(attacker - attacker * guard // (2 * total), 1)
            remaining = defender - min(attacker, defender)
            if remaining:
                target.soldiers = remaining
                source.soldiers -= attacker - survivors
                _settle(source)
                self._log(
                    f"{player.name} attacked {where} {attacker} vs {defender}: won the exchange, "
                    f"{remaining} defenders hold, attacker down to {survivors}"
                )
                return
            loot = target.loot if target.kind == TileKind.LAND and target.owner is None else 0
            gold = GOLD_PER_BOT if target.kind == TileKind.LAND and target.owner is None else 0
            target.owner = player.id
            target.soldiers = survivors + loot
            player.gold += gold
            source.soldiers -= attacker
            _settle(source)
            line = f"{player.name} took {where} {attacker} vs {defender}: {survivors} soldiers"
            if loot:
                line += f", looted {loot}"
            if gold:
                line += f", seized {gold} gold"
            self._log(line + _raze(target))
            return
        source.soldiers -= ceil(attacker * guard / total)
        _settle(source)
        target.soldiers = defender - attacker * guard // (2 * total)
        self._log(
            f"{player.name} attacked {where} {attacker} vs {defender}: repelled, "
            f"attacker down to {source.soldiers}, defenders down to {target.soldiers}"
        )

    def _prune_orders(self) -> None:
        kept = []
        for order in self.game.orders:
            if self.tile(order.source).owner == order.player:
                kept.append(order)
                continue
            player = self._find(order.player)
            if player is not None:
                self._log(f"{player.name}'s plan at {_label(order.source)} fell through")
        self.game.orders = kept

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
                        tile.buildings = []

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
                if tile.kind != TileKind.LAND or tile.owner is None:
                    continue
                tile.soldiers += PRODUCTION
                if BuildingKind.FARM in tile.buildings:
                    tile.soldiers += FARM_BONUS

    def _log(self, line: str) -> None:
        self.game.log.append(line)
        del self.game.log[:-LOG_LIMIT]
