import random

import pytest

from game import bot
from game.constants import BOT_FARM_FLOOR, BOT_FORT_FLOOR, BOT_NAMES, BUILDING_COST
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
    alice.capital = None
    bob.capital = None
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


def roll(monkeypatch, value):
    monkeypatch.setattr(random, "random", lambda: value)


def test_even_odds_are_taken_half_the_time(monkeypatch):
    state, alice, _ = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 200)
    state.tile(Coord(x=1, y=0)).soldiers = 200

    roll(monkeypatch, 0.49)
    assert plan(state, alice).orders

    roll(monkeypatch, 0.5)
    assert plan(state, alice).orders == []


def test_a_desperate_attack_is_still_on_the_table(monkeypatch):
    state, alice, _ = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 40)
    state.tile(Coord(x=1, y=0)).soldiers = 200

    roll(monkeypatch, 0.1)
    assert plan(state, alice).orders

    roll(monkeypatch, 0.5)
    assert plan(state, alice).orders == []


def test_a_fort_halves_the_odds(monkeypatch):
    state, alice, bob = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 200)
    put(state, bob, 1, 0, 100, BuildingKind.FORT)

    roll(monkeypatch, 0.6)
    assert plan(state, alice).orders == []

    state.tile(Coord(x=1, y=0)).buildings = []

    assert plan(state, alice).orders


def test_a_free_tile_outweighs_a_contested_one(monkeypatch):
    state, alice, _ = table()
    put(state, alice, 0, 0, 100)
    free = state.tile(Coord(x=1, y=0))
    free.soldiers = 0
    free.loot = 0
    state.tile(Coord(x=0, y=1)).soldiers = 100

    roll(monkeypatch, 0.3)
    assert plan(state, alice).orders[0].target == Coord(x=1, y=0)

    roll(monkeypatch, 0.9)
    assert plan(state, alice).orders[0].target == Coord(x=0, y=1)


def test_a_tie_is_split_by_the_pile(monkeypatch):
    state, alice, _ = table()
    wet(state, 1, 1)
    put(state, alice, 1, 0, 150)
    state.tile(Coord(x=0, y=0)).loot = 40
    state.tile(Coord(x=2, y=0)).loot = 60

    roll(monkeypatch, 0.1)
    assert plan(state, alice).orders[0].target == Coord(x=2, y=0)

    roll(monkeypatch, 0.5)
    assert plan(state, alice).orders[0].target == Coord(x=0, y=0)


def test_no_neighbour_means_no_strike():
    state, alice, _ = table()
    wet(state, 0, 1)
    wet(state, 1, 0)
    put(state, alice, 0, 0, 100)

    assert bot._strike(state.game, alice.id, 0, 0, 100) == []


def test_the_back_of_a_block_pushes_forward(monkeypatch):
    state, alice, _ = table()
    block(state, alice)
    roll(monkeypatch, 0.0)

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


def test_every_tile_acts_once(monkeypatch):
    state, alice, _ = table()
    block(state, alice)
    roll(monkeypatch, 0.0)

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


def test_a_stack_on_the_water_can_land(monkeypatch):
    state, alice, _ = table()
    roll(monkeypatch, 0.0)
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


def test_a_fort_goes_up_on_the_tile_that_cannot_push(monkeypatch):
    state, alice, bob = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 150)
    put(state, bob, 1, 0, 100, BuildingKind.FORT)
    alice.gold = BOT_FORT_FLOOR
    roll(monkeypatch, 0.9)

    assert plan(state, alice).builds == [(Coord(x=0, y=0), BuildingKind.FORT)]


def test_no_fort_when_the_enemy_is_too_strong(monkeypatch):
    state, alice, bob = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 40)
    put(state, bob, 1, 0, 100, BuildingKind.FORT)
    alice.gold = BOT_FORT_FLOOR
    roll(monkeypatch, 0.9)

    assert plan(state, alice).builds == []


@pytest.mark.parametrize("garrison, built", [(120, True), (100, False)])
def test_the_whole_neighbourhood_counts_for_the_fort(garrison, built, monkeypatch):
    state, alice, bob = table()
    put(state, alice, 0, 0, garrison)
    put(state, bob, 1, 0, 110, BuildingKind.FORT)
    put(state, bob, 0, 1, 110, BuildingKind.FORT)
    alice.gold = BOT_FORT_FLOOR
    roll(monkeypatch, 0.9)

    assert bool(plan(state, alice).builds) is built


def test_a_neutral_is_no_reason_to_fortify(monkeypatch):
    state, alice, _ = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 150)
    state.tile(Coord(x=1, y=0)).soldiers = 200
    alice.gold = BOT_FORT_FLOOR
    roll(monkeypatch, 0.9)

    assert plan(state, alice).builds == []


def test_a_fort_is_never_built_on_water(monkeypatch):
    state, alice, bob = table()
    lake = wet(state, 1, 0)
    lake.owner = alice.id
    lake.soldiers = 100
    put(state, bob, 2, 0, 90, BuildingKind.FORT)
    put(state, alice, 0, 0, 100)
    alice.gold = BOT_FORT_FLOOR
    roll(monkeypatch, 0.9)

    assert all(coord != Coord(x=1, y=0) for coord, _ in plan(state, alice).builds)


@pytest.mark.parametrize("gold, built", [(BOT_FORT_FLOOR, True), (BOT_FORT_FLOOR - 1, False)])
def test_a_fort_keeps_the_reserve(gold, built, monkeypatch):
    state, alice, bob = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 150)
    put(state, bob, 1, 0, 100, BuildingKind.FORT)
    alice.gold = gold
    roll(monkeypatch, 0.9)

    assert bool(plan(state, alice).builds) is built


def test_a_fort_is_not_repeated(monkeypatch):
    state, alice, bob = table()
    wet(state, 0, 1)
    put(state, alice, 0, 0, 150, BuildingKind.FORT)
    put(state, bob, 1, 0, 100, BuildingKind.FORT)
    alice.gold = BOT_FORT_FLOOR
    roll(monkeypatch, 0.9)

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
    assert alice.gold == BOT_FARM_FLOOR * 2 - len(farms) * BUILDING_COST


def test_a_fort_is_paid_for_before_a_farm(monkeypatch):
    state, alice, bob = table()
    block(state, alice)
    put(state, bob, 3, 0, 100, BuildingKind.FORT)
    alice.bot = True
    alice.gold = BOT_FARM_FLOOR + BUILDING_COST
    roll(monkeypatch, 0.9)

    state.plan_bots()

    assert state.tile(Coord(x=2, y=0)).buildings == [BuildingKind.FORT]
    assert state.tile(Coord(x=0, y=0)).buildings == [BuildingKind.FARM]
    assert alice.gold == BOT_FORT_FLOOR


def test_a_lost_capital_pulls_the_whole_plan_back(monkeypatch):
    state, alice, bob = table()
    alice.capital = Coord(x=0, y=0)
    put(state, alice, 5, 5, 200)
    put(state, bob, 0, 0, 100)
    alice.bot = True
    roll(monkeypatch, 0.0)

    state.plan_bots()

    assert state.game.orders[0].target == Coord(x=4, y=5)


def test_a_lost_capital_outranks_a_soft_neighbour(monkeypatch):
    state, alice, bob = table()
    alice.capital = Coord(x=0, y=0)
    put(state, alice, 5, 5, 200)
    put(state, bob, 6, 5, 10)
    put(state, bob, 0, 0, 100)
    alice.bot = True
    roll(monkeypatch, 0.0)

    state.plan_bots()

    assert state.game.orders[0].target == Coord(x=4, y=5)


def test_a_held_capital_leaves_the_plan_alone(monkeypatch):
    state, alice, bob = table()
    alice.capital = Coord(x=0, y=0)
    put(state, alice, 5, 5, 200)
    put(state, alice, 0, 0, 200)
    put(state, bob, 6, 5, 10)
    alice.bot = True
    roll(monkeypatch, 0.0)

    state.plan_bots()

    targets = [
        order.target for order in state.game.orders if (order.source.x, order.source.y) == (5, 5)
    ]
    assert Coord(x=6, y=5) in targets


def test_a_rich_tile_splits_across_two_cheap_neighbours(monkeypatch):
    state, alice, _ = table()
    wet(state, 1, 1)
    put(state, alice, 1, 0, 300)
    state.tile(Coord(x=0, y=0)).soldiers = 60
    state.tile(Coord(x=2, y=0)).soldiers = 90
    roll(monkeypatch, 0.0)

    targets = plan(state, alice).orders

    assert [(order.target, order.soldiers) for order in targets] == [
        (Coord(x=0, y=0), 150),
        (Coord(x=2, y=0), 150),
    ]


def test_a_split_stops_at_the_guard_it_cannot_afford(monkeypatch):
    state, alice, _ = table()
    wet(state, 1, 1)
    put(state, alice, 1, 0, 300)
    state.tile(Coord(x=0, y=0)).soldiers = 60
    state.tile(Coord(x=2, y=0)).soldiers = 90
    state.tile(Coord(x=1, y=1)).kind = TileKind.LAND
    state.tile(Coord(x=1, y=1)).soldiers = 200
    roll(monkeypatch, 0.0)

    assert len(plan(state, alice).orders) == 2


def test_a_poor_tile_strikes_once(monkeypatch):
    state, alice, _ = table()
    wet(state, 1, 1)
    put(state, alice, 1, 0, 200)
    state.tile(Coord(x=0, y=0)).soldiers = 150
    state.tile(Coord(x=2, y=0)).soldiers = 150
    roll(monkeypatch, 0.0)

    assert len(plan(state, alice).orders) == 1


def test_a_split_takes_everything_it_can(monkeypatch):
    state, alice, _ = table()
    wet(state, 1, 1)
    put(state, alice, 1, 0, 400)
    state.tile(Coord(x=0, y=0)).soldiers = 50
    state.tile(Coord(x=2, y=0)).soldiers = 50
    state.tile(Coord(x=1, y=1)).kind = TileKind.LAND
    state.tile(Coord(x=1, y=1)).soldiers = 50
    roll(monkeypatch, 0.0)

    orders = plan(state, alice).orders

    assert len(orders) == 3
    assert all(order.soldiers == 133 for order in orders)


def test_a_split_rolls_against_its_own_share(monkeypatch):
    state, alice, _ = table()
    wet(state, 1, 1)
    put(state, alice, 1, 0, 300)
    state.tile(Coord(x=0, y=0)).soldiers = 60
    state.tile(Coord(x=2, y=0)).soldiers = 90

    roll(monkeypatch, 0.5)
    assert plan(state, alice).orders

    roll(monkeypatch, 0.8)
    assert plan(state, alice).orders == []


def test_a_split_is_planned_as_one_plan(monkeypatch):
    state, alice, _ = table()
    wet(state, 1, 1)
    put(state, alice, 1, 0, 300)
    state.tile(Coord(x=0, y=0)).soldiers = 60
    state.tile(Coord(x=2, y=0)).soldiers = 90
    roll(monkeypatch, 0.0)

    assert plan(state, alice) == plan(state, alice)


def test_a_bot_split_lands_through_the_state(monkeypatch):
    state, alice, _ = table()
    wet(state, 1, 1)
    put(state, alice, 1, 0, 300)
    state.tile(Coord(x=0, y=0)).soldiers = 60
    state.tile(Coord(x=2, y=0)).soldiers = 90
    alice.bot = True
    roll(monkeypatch, 0.0)

    state.plan_bots()

    assert [(order.target, order.soldiers) for order in state.game.orders] == [
        (Coord(x=0, y=0), 150),
        (Coord(x=2, y=0), 150),
    ]


def test_a_bot_split_is_not_a_standing_order(monkeypatch):
    state, alice, _ = table()
    wet(state, 1, 1)
    put(state, alice, 1, 0, 300)
    state.tile(Coord(x=0, y=0)).soldiers = 60
    state.tile(Coord(x=2, y=0)).soldiers = 90
    alice.bot = True
    roll(monkeypatch, 0.0)

    state.plan_bots()

    assert all(order.repeat is False for order in state.game.orders)


def test_the_homeland_is_the_quarter_around_the_capital():
    assert bot._homeland(10, Coord(x=0, y=0)) == (0, 4, 0, 4)
    assert bot._homeland(10, Coord(x=9, y=9)) == (6, 10, 6, 10)
    assert bot._homeland(10, Coord(x=9, y=0)) == (6, 10, 0, 4)
    assert bot._homeland(10, Coord(x=0, y=9)) == (0, 4, 6, 10)


def test_a_homeland_target_gets_a_second_roll():
    home = bot._homeland(10, Coord(x=0, y=0))

    assert bot._urge(200, 200, home, 1, 1) == 1.0
    assert bot._urge(200, 200, home, 7, 7) == 0.5
    assert bot._urge(200, 200, None, 1, 1) == 0.5


def test_a_homeland_target_is_taken_at_double_the_odds(monkeypatch):
    state, alice, _ = table()
    alice.capital = Coord(x=0, y=0)
    wet(state, 0, 1)
    put(state, alice, 0, 0, 200)
    state.tile(Coord(x=1, y=0)).soldiers = 200
    roll(monkeypatch, 0.9)

    assert plan(state, alice).orders[0].target == Coord(x=1, y=0)


def test_the_same_odds_outside_the_homeland_hold(monkeypatch):
    state, alice, _ = table()
    alice.capital = Coord(x=0, y=0)
    put(state, alice, 0, 0, 0)
    put(state, alice, 6, 6, 200)
    wet(state, 5, 6)
    wet(state, 6, 7)
    wet(state, 6, 5)
    state.tile(Coord(x=7, y=6)).soldiers = 200
    roll(monkeypatch, 0.9)

    assert plan(state, alice).orders == []


def test_the_field_halves_the_cost_of_homeland_ground():
    state, alice, bob = table()
    alice.capital = Coord(x=0, y=0)
    home = bot._homeland(10, alice.capital)
    for row in state.game.tiles:
        for tile in row:
            tile.owner = alice.id
    put(state, bob, 0, 3, 100)
    put(state, bob, 6, 3, 100)

    dist = bot._distances(state.game, alice.id, alice.capital, home)

    assert dist[3][3] == 3
    assert bot._step(dist, 3, 3, 10) == (2, 3)


def test_a_bot_order_never_stands(monkeypatch):
    state, alice, _ = table()
    block(state, alice)
    alice.bot = True
    roll(monkeypatch, 0.0)

    state.plan_bots()

    assert state.game.orders
    assert all(order.repeat is False for order in state.game.orders)


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


def test_the_plan_is_the_same_every_time(monkeypatch):
    state, alice, bob = table()
    block(state, alice)
    put(state, bob, 3, 0, 100, BuildingKind.FORT)
    alice.gold = BOT_FARM_FLOOR + BUILDING_COST
    roll(monkeypatch, 0.0)

    assert plan(state, alice) == plan(state, alice)


def test_a_new_plan_replaces_the_old_orders(monkeypatch):
    state, alice, _ = table()
    put(state, alice, 0, 0, 150)
    alice.bot = True
    roll(monkeypatch, 0.0)
    state.plan_bots()
    assert len(state.game.orders) == 1

    state.game.tiles[0][0].owner = None
    state.plan_bots()

    assert state.game.orders == []


def test_the_plan_follows_the_board(monkeypatch):
    state, alice, _ = table()
    put(state, alice, 0, 0, 200)
    alice.bot = True
    roll(monkeypatch, 0.0)
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


def test_kick_clears_a_seat():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    bob = state.join("bob", PlayerColor.BLUE)

    state.kick(bob.id)

    assert state.game.players == [alice]
    assert "bob left the table" in state.game.log


def test_kick_clears_a_bot():
    state = State()
    state.join("alice", PlayerColor.RED)
    seated = state.add_bot()

    state.kick(seated.id)

    assert len(state.game.players) == 1


def test_a_kicked_name_is_free_again():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    state.kick(alice.id)

    again = state.join("alice", PlayerColor.RED)

    assert again.name == "alice"
    assert len(state.game.players) == 1


def test_kick_needs_a_known_seat():
    state = State()

    with pytest.raises(StateError, match="not in this game"):
        state.kick("nobody")


def test_kick_is_refused_once_the_game_is_on():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    bob = state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, 10)

    with pytest.raises(StateError, match="already started"):
        state.kick(bob.id)

    assert len(state.game.players) == 2


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
