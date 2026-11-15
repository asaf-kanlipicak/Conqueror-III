from collections import deque
from dataclasses import dataclass, field

from game.constants import BOT_FARM_FLOOR, BOT_FORT_RATIO, BUILDING_COST, FORT_DEFENSE
from game.enums import BuildingKind, TileKind
from game.models import Coord, Game, PendingOrder, Player, Tile

STEPS = ((1, 0), (0, 1), (-1, 0), (0, -1))


@dataclass
class Plan:
    orders: list[PendingOrder] = field(default_factory=list)
    builds: list[tuple[Coord, BuildingKind]] = field(default_factory=list)


def think(game: Game, player: Player) -> Plan:
    me = player.id
    size = game.size
    dist = _distances(game, me)
    plan = Plan()
    held: list[tuple[int, int]] = []

    for y in range(size):
        for x in range(size):
            tile = game.tiles[y][x]
            if tile.owner != me or tile.soldiers == 0:
                continue
            here = dist[y][x]
            if here < 0:
                continue
            if here == 1:
                target = _strike(game, me, x, y, tile.soldiers)
                if target is None:
                    held.append((x, y))
                else:
                    plan.orders.append(
                        PendingOrder(
                            player=me,
                            source=Coord(x=x, y=y),
                            target=target,
                            soldiers=tile.soldiers,
                        )
                    )
                continue
            step = _step(dist, x, y, size)
            if step is not None:
                plan.orders.append(
                    PendingOrder(
                        player=me,
                        source=Coord(x=x, y=y),
                        target=Coord(x=step[0], y=step[1]),
                        soldiers=tile.soldiers,
                    )
                )

    gold = player.gold
    fort = _fort(game, me, held, gold)
    if fort is not None:
        plan.builds.append((fort, BuildingKind.FORT))
        gold -= BUILDING_COST
    for coord in _farms(game, me, dist, gold):
        plan.builds.append((coord, BuildingKind.FARM))
    return plan


def _around(x: int, y: int, size: int):
    for dx, dy in STEPS:
        nx, ny = x + dx, y + dy
        if 0 <= nx < size and 0 <= ny < size:
            yield nx, ny


def _target(tile: Tile, me: str) -> bool:
    if tile.owner == me:
        return False
    return tile.kind == TileKind.LAND or tile.soldiers > 0


def _guard(tile: Tile) -> int:
    return tile.soldiers * FORT_DEFENSE if BuildingKind.FORT in tile.buildings else tile.soldiers


def _distances(game: Game, me: str) -> list[list[int]]:
    size = game.size
    dist = [[-1] * size for _ in range(size)]
    queue: deque[tuple[int, int]] = deque()
    for y in range(size):
        for x in range(size):
            if _target(game.tiles[y][x], me):
                dist[y][x] = 0
                queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        for nx, ny in _around(x, y, size):
            if dist[ny][nx] == -1:
                dist[ny][nx] = dist[y][x] + 1
                queue.append((nx, ny))
    return dist


def _strike(game: Game, me: str, x: int, y: int, soldiers: int) -> Coord | None:
    best = None
    for nx, ny in _around(x, y, game.size):
        tile = game.tiles[ny][nx]
        if not _target(tile, me):
            continue
        guard = _guard(tile)
        if soldiers < guard:
            continue
        key = (guard, -tile.loot, ny, nx)
        if best is None or key < best[0]:
            best = (key, Coord(x=nx, y=ny))
    return best[1] if best else None


def _step(dist: list[list[int]], x: int, y: int, size: int) -> tuple[int, int] | None:
    here = dist[y][x]
    best = None
    for nx, ny in _around(x, y, size):
        there = dist[ny][nx]
        if there < 0 or there >= here:
            continue
        if best is None or there < best[0]:
            best = (there, nx, ny)
    return (best[1], best[2]) if best else None


def _fort(game: Game, me: str, held: list[tuple[int, int]], gold: int) -> Coord | None:
    if gold < BUILDING_COST:
        return None
    best = None
    for x, y in held:
        tile = game.tiles[y][x]
        if tile.kind != TileKind.LAND or BuildingKind.FORT in tile.buildings:
            continue
        enemy = sum(
            game.tiles[ny][nx].soldiers
            for nx, ny in _around(x, y, game.size)
            if game.tiles[ny][nx].owner not in (None, me)
        )
        if enemy == 0 or enemy > tile.soldiers * BOT_FORT_RATIO:
            continue
        if best is None or tile.soldiers > game.tiles[best[1]][best[0]].soldiers:
            best = (x, y)
    return Coord(x=best[0], y=best[1]) if best else None


def _farms(game: Game, me: str, dist: list[list[int]], gold: int) -> list[Coord]:
    spots = [
        (dist[y][x], game.tiles[y][x].soldiers, y, x)
        for y in range(game.size)
        for x in range(game.size)
        if game.tiles[y][x].owner == me
        and game.tiles[y][x].kind == TileKind.LAND
        and BuildingKind.FARM not in game.tiles[y][x].buildings
    ]
    spots.sort(key=lambda spot: (-spot[0], -spot[1], spot[2], spot[3]))
    picked = []
    while gold >= BOT_FARM_FLOOR and spots:
        _, _, y, x = spots.pop(0)
        picked.append(Coord(x=x, y=y))
        gold -= BUILDING_COST
    return picked
