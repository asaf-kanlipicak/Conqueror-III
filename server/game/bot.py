import random
from dataclasses import dataclass, field
from heapq import heappop, heappush

from game.constants import (
    BOT_FARM_FLOOR,
    BOT_FORT_FLOOR,
    BOT_FORT_RATIO,
    BUILDING_COST,
    FORT_DEFENSE,
    HOMELAND_URGE,
    RIVER_WIDTH,
)
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
    home = _homeland(size, player.capital) if player.capital is not None else None
    dist = _distances(game, me, player.capital, home)
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
            if any(dist[ny][nx] == 0 for nx, ny in _around(x, y, size)):
                targets = _strike(game, me, x, y, tile.soldiers, home)
                if not targets:
                    held.append((x, y))
                for target in targets:
                    plan.orders.append(
                        PendingOrder(
                            player=me,
                            source=Coord(x=x, y=y),
                            target=target,
                            soldiers=tile.soldiers // len(targets),
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


def _homeland(size: int, capital: Coord) -> tuple[int, int, int, int]:
    start = (size - RIVER_WIDTH) // 2
    end = start + RIVER_WIDTH
    x0, x1 = (0, start) if capital.x < start else (end, size)
    y0, y1 = (0, start) if capital.y < start else (end, size)
    return x0, x1, y0, y1


def _home(home: tuple[int, int, int, int] | None, x: int, y: int) -> bool:
    if home is None:
        return False
    x0, x1, y0, y1 = home
    return x0 <= x < x1 and y0 <= y < y1


def _distances(
    game: Game,
    me: str,
    capital: Coord | None = None,
    home: tuple[int, int, int, int] | None = None,
) -> list[list[int]]:
    size = game.size
    dist = [[-1] * size for _ in range(size)]
    heap: list[tuple[int, int, int]] = []

    def push(col: int, row: int, weight: int) -> None:
        if dist[row][col] == -1 or weight < dist[row][col]:
            dist[row][col] = weight
            heappush(heap, (weight, row, col))

    if capital is not None and game.tiles[capital.y][capital.x].owner != me:
        push(capital.x, capital.y, 0)
    else:
        for y in range(size):
            for x in range(size):
                if _target(game.tiles[y][x], me):
                    push(x, y, 0)
    while heap:
        cost, y, x = heappop(heap)
        if cost > dist[y][x]:
            continue
        for nx, ny in _around(x, y, size):
            step = 1 if _home(home, nx, ny) else 2
            if dist[ny][nx] == -1 or cost + step < dist[ny][nx]:
                dist[ny][nx] = cost + step
                heappush(heap, (cost + step, ny, nx))
    return dist


def _strike(
    game: Game,
    me: str,
    x: int,
    y: int,
    soldiers: int,
    home: tuple[int, int, int, int] | None = None,
) -> list[Coord]:
    targets = []
    for nx, ny in _around(x, y, game.size):
        tile = game.tiles[ny][nx]
        if _target(tile, me):
            targets.append((-_urge(soldiers, _guard(tile), home, nx, ny), -tile.loot, ny, nx))
    if not targets or soldiers < 1:
        return []
    targets.sort()
    chosen: list[Coord] = []
    for _, _, ny, nx in targets:
        share = soldiers // (len(chosen) + 1)
        if share < 1:
            break
        if random.random() >= _urge(share, _guard(game.tiles[ny][nx]), home, nx, ny):
            continue
        chosen.append(Coord(x=nx, y=ny))
    return chosen


def _urge(
    soldiers: int, guard: int, home: tuple[int, int, int, int] | None, x: int, y: int
) -> float:
    chance = soldiers / (soldiers + guard)
    if _home(home, x, y):
        chance *= HOMELAND_URGE
    return min(1.0, chance)


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
    if gold < BOT_FORT_FLOOR:
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
