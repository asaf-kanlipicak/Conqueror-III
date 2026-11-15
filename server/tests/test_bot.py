import random

import pytest

from game import bot
from game.constants import BOT_FARM_FLOOR, BOT_NAMES, BUILDING_COST
from game.enums import BuildingKind, PlayerColor, TileKind
from game.models import Coord, Tile
from game.state import State, StateError


def board(size=10, garrison=100):
    return [
        [Tile(soldiers=garrison, loot=garrison // 2) for _ in range(size)] for _ in range(size)
    ]


def table(size=10, garrison=100):
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    bob = state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, size)
    state.game.tiles = board(size, garrison)
    return state, alice, bob


def put(state, player, x, y, soldiers, *buildings):
    tile = state.tile(Coord(x=x, y=y))
    tile.owner = player.id
    tile.soldiers = soldiers
    tile.buildings = list(buildings)
    return tile


def wet(state, x, y):
    tile = state.tile(Coord(x=x, y=y))
    tile.kind = TileKind.WATER
    tile.owner = None
    tile.soldiers = 0
    tile.loot = 0
    return tile


def block(state, player, soldiers=100):
    for y in range(3):
        for x in range(3):
            put(state, player, x, y, soldiers)


def plan(state, player):
    return bot.think(state.game, player)


def moves(state, player):
    return {(o.source.x, o.source.y): (o.target.x, o.target.y) for o in plan(state, player).orders}


def test_a_frontier_tile_takes_the_cheapest_neighbour():
    state, alice, _ = table()
    put(state, alice, 0, 0, 200)
    state.tile(Coord(x=0, y=1)).soldiers = 150

    result = plan(state, alice)

    assert [(order.target, order.soldiers) for order in result.orders] == [(Coord(x=1, y=0), 200)]


def test_a_tie_goes_to_the_richer_pile():
    state, alice, _ = table()
    put(state, alice, 1, 0, 200)
    state.tile(Coord(x=0, y=0)).loot = 40
    state.tile(Coord(x=2, y=0)).loot = 60

    assert plan(state, alice).orders[0].target == Coord(x=2, y=0)


def test_a_tile_that_cannot_break_even_holds():
    state, alice, _ = table()
    put(state, alice, 0, 0, 99)

    assert plan(state, alice).orders == []


@pytest.mark.parametrize("soldiers, attacks", [(200, True), (199, False)])
def test_a_fort_has_to_be_doubled_before_it_is_attacked(soldiers, attacks):
    state, alice, bob = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, soldiers)
    put(state, bob, 1, 0, 100, BuildingKind.FORT)

    assert bool(plan(state, alice).orders) is attacks


def test_the_back_of_a_block_pushes_forward():
    state, alice, _ = table()
    block(state, alice)

    flow = moves(state, alice)

    assert flow[(0, 0)] == (1, 0)
    assert flow[(1, 1)] == (2, 1)
    assert flow[(2, 0)] == (3, 0)


def test_the_flow_never_runs_backwards():
    state, alice, _ = table()
    block(state, alice)
    dist = bot._distances(state.game, alice.id)

    for order in plan(state, alice).orders:
        assert dist[order.target.y][order.target.x] < dist[order.source.y][order.source.x]


def test_every_tile_acts_once():
    state, alice, _ = table()
    block(state, alice)

    result = plan(state, alice)

    assert len(result.orders) == 9
    assert len({(order.source.x, order.source.y) for order in result.orders}) == 9


def test_open_water_is_a_bridge():
    state, alice, _ = table()
    state.game.tiles = [[Tile(kind=TileKind.WATER) for _ in range(10)] for _ in range(10)]
    put(state, alice, 0, 0, 100)
    shore = state.tile(Coord(x=2, y=0))
    shore.kind = TileKind.LAND
    shore.soldiers = 50
    shore.loot = 25

    assert [(order.source, order.target) for order in plan(state, alice).orders] == [
        (Coord(x=0, y=0), Coord(x=1, y=0))
    ]


def test_a_stack_on_the_water_can_land():
    state, alice, _ = table()
    state.game.tiles = [[Tile(kind=TileKind.WATER) for _ in range(10)] for _ in range(10)]
    put(state, alice, 0, 0, 100)
    lake = state.tile(Coord(x=1, y=0))
    lake.owner = alice.id
    lake.soldiers = 100
    shore = state.tile(Coord(x=2, y=0))
    shore.kind = TileKind.LAND
    shore.soldiers = 50
    shore.loot = 25

    flow = moves(state, alice)

    assert flow[(1, 0)] == (2, 0)
    assert flow[(0, 0)] == (1, 0)


def test_a_board_with_nothing_left_to_take_is_quiet():
    state, alice, _ = table()
    for row in state.game.tiles:
        for tile in row:
            tile.owner = alice.id
            tile.soldiers = 50

    assert plan(state, alice).orders == []


def test_a_fort_goes_up_on_the_tile_that_cannot_push():
    state, alice, bob = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 150)
    put(state, bob, 1, 0, 100, BuildingKind.FORT)
    alice.gold = BUILDING_COST

    assert plan(state, alice).builds == [(Coord(x=0, y=0), BuildingKind.FORT)]


def test_no_fort_when_the_enemy_is_too_strong():
    state, alice, bob = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 40)
    put(state, bob, 1, 0, 100, BuildingKind.FORT)
    alice.gold = BUILDING_COST

    assert plan(state, alice).builds == []


@pytest.mark.parametrize("garrison, built", [(120, True), (100, False)])
def test_the_whole_neighbourhood_counts_for_the_fort(garrison, built):
    state, alice, bob = table()
    put(state, alice, 0, 0, garrison)
    put(state, bob, 1, 0, 110, BuildingKind.FORT)
    put(state, bob, 0, 1, 110, BuildingKind.FORT)
    alice.gold = BUILDING_COST

    assert bool(plan(state, alice).builds) is built


def test_a_neutral_is_no_reason_to_fortify():
    state, alice, _ = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 150)
    state.tile(Coord(x=1, y=0)).soldiers = 200
    alice.gold = BUILDING_COST

    assert plan(state, alice).builds == []


def test_a_fort_is_never_built_on_water():
    state, alice, bob = table()
    lake = wet(state, 1, 0)
    lake.owner = alice.id
    lake.soldiers = 100
    put(state, bob, 2, 0, 90, BuildingKind.FORT)
    put(state, alice, 0, 0, 100)
    alice.gold = BUILDING_COST

    assert all(coord != Coord(x=1, y=0) for coord, _ in plan(state, alice).builds)


def test_a_fort_needs_the_gold():
    state, alice, bob = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 150)
    put(state, bob, 1, 0, 100, BuildingKind.FORT)
    alice.gold = BUILDING_COST - 1

    assert plan(state, alice).builds == []


def test_a_fort_is_not_repeated():
    state, alice, bob = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 150, BuildingKind.FORT)
    put(state, bob, 1, 0, 100, BuildingKind.FORT)
    alice.gold = BUILDING_COST

    assert plan(state, alice).builds == []


def test_a_farm_goes_deep_and_keeps_the_reserve():
    state, alice, _ = table()
    block(state, alice)
    alice.gold = BOT_FARM_FLOOR

    assert plan(state, alice).builds == [(Coord(x=0, y=0), BuildingKind.FARM)]


def test_a_farm_waits_for_the_reserve():
    state, alice, _ = table()
    block(state, alice)
    alice.gold = BOT_FARM_FLOOR - 1

    assert plan(state, alice).builds == []


def test_spare_gold_buys_several_farms():
    state, alice, _ = table()
    block(state, alice)
    alice.bot = True
    alice.gold = BOT_FARM_FLOOR * 2

    state.plan_bots()

    farms = [
        tile
        for row in state.game.tiles
        for tile in row
        if BuildingKind.FARM in tile.buildings
    ]
    assert len(farms) == 3
    assert alice.gold == BUILDING_COST


def test_a_fort_is_paid_for_before_a_farm():
    state, alice, bob = table()
    block(state, alice)
    put(state, bob, 3, 0, 100, BuildingKind.FORT)
    alice.bot = True
    alice.gold = BOT_FARM_FLOOR + BUILDING_COST

    state.plan_bots()

    assert state.tile(Coord(x=2, y=0)).buildings == [BuildingKind.FORT]
    assert state.tile(Coord(x=0, y=0)).buildings == [BuildingKind.FARM]
    assert alice.gold == BUILDING_COST


def test_a_bot_never_builds_twice_on_one_tile():
    state, alice, _ = table()
    block(state, alice)
    alice.bot = True
    alice.gold = BOT_FARM_FLOOR * 4

    state.plan_bots()
    first = alice.gold
    state.plan_bots()

    assert alice.gold == first
    assert all(len(tile.buildings) == 1 for row in state.game.tiles for tile in row if tile.buildings)


def test_a_bot_does_not_build_on_someone_elses_turn():
    state, alice, _ = table()
    block(state, alice)
    alice.bot = True
    alice.gold = BOT_FARM_FLOOR
    state.game.turn = 1

    state.plan_bots()

    assert state.game.orders
    assert state.tile(Coord(x=0, y=0)).buildings == []
    assert alice.gold == BOT_FARM_FLOOR


def test_the_plan_is_the_same_every_time():
    state, alice, bob = table()
    block(state, alice)
    put(state, bob, 3, 0, 100, BuildingKind.FORT)
    alice.gold = BOT_FARM_FLOOR + BUILDING_COST

    assert plan(state, alice) == plan(state, alice)


def test_a_new_plan_replaces_the_old_orders():
    state, alice, _ = table()
    put(state, alice, 0, 0, 200)
    alice.bot = True
    state.plan_bots()
    assert len(state.game.orders) == 1

    state.game.tiles[0][0].owner = None
    state.plan_bots()

    assert state.game.orders == []


def test_the_plan_follows_the_board():
    state, alice, _ = table()
    put(state, alice, 0, 0, 200)
    alice.bot = True
    state.plan_bots()
    assert state.game.orders[0].target == Coord(x=1, y=0)

    state.tile(Coord(x=1, y=0)).soldiers = 400
    state.plan_bots()

    assert state.game.orders[0].target == Coord(x=0, y=1)


def test_no_plan_before_the_game_starts():
    state = State()
    alice = state.add_bot()
    state.join("bob", PlayerColor.BLUE)

    state.plan_bots()

    assert state.game.orders == []
    assert alice.gold == 0


def test_an_eliminated_bot_is_skipped():
    state, alice, _ = table()
    put(state, alice, 0, 0, 200)
    alice.bot = True
    alice.eliminated = True

    state.plan_bots()

    assert state.game.orders == []


def test_add_bot_seats_one_with_a_free_colour():
    state = State()
    alice = state.join("alice", PlayerColor.RED)

    first = state.add_bot()
    second = state.add_bot()

    assert first.bot is True and second.bot is True
    assert first.name != second.name
    assert {first.name, second.name} <= set(BOT_NAMES)
    assert {first.color, second.color} == {PlayerColor.GREEN, PlayerColor.BLUE}
    assert alice in state.game.players
    assert f"{first.name} joined as {first.color}" in state.game.log


def test_add_bot_respects_the_table():
    state = State()
    state.join("alice", PlayerColor.RED)
    state.add_bot()
    state.add_bot()
    state.add_bot()

    with pytest.raises(StateError, match="game is full"):
        state.add_bot()

    state.start(None, 10)

    with pytest.raises(StateError, match="already started"):
        state.add_bot()


def test_a_bot_never_takes_a_seated_name():
    state = State()
    state.join(BOT_NAMES[0], PlayerColor.RED)

    seated = state.add_bot()

    assert seated.name != BOT_NAMES[0]
    assert seated.name in BOT_NAMES


def test_a_bot_name_is_drawn_from_the_free_ones(monkeypatch):
    state = State()
    state.join(BOT_NAMES[0], PlayerColor.RED)
    monkeypatch.setattr(random, "choice", lambda names: names[-1])

    assert state.add_bot().name == BOT_NAMES[-1]


def test_a_full_table_gets_four_different_names():
    state = State()

    names = [state.add_bot().name for _ in range(4)]

    assert len(set(names)) == 4
    assert set(names) <= set(BOT_NAMES)


def test_a_bystander_can_start_the_table():
    state = State()
    state.join("alice", PlayerColor.RED)
    state.add_bot()

    state.start(None, 10)

    assert state.game.started
    assert len(state.game.players) == 2


def test_a_bystander_can_lay_out_the_map():
    state = State()
    state.add_bot()
    state.add_bot()

    state.shape(None, 10)

    assert state.game.size == 10
    assert len(state.game.tiles) == 10


def test_shape_still_rejects_an_unknown_seat():
    state = State()
    state.join("alice", PlayerColor.RED)

    with pytest.raises(StateError, match="not in this game"):
        state.shape("nobody", 10)

    assert state.game.size == 20


def test_start_still_rejects_an_unknown_seat():
    state = State()
    state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)

    with pytest.raises(StateError, match="not in this game"):
        state.start("nobody")

    assert not state.game.started
