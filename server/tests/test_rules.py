import random
from math import ceil

import pytest

from game import state as state_module
from game.constants import (
    BUILDING_COST,
    CAPITAL_GARRISON,
    CHAT_LIMIT,
    CHAT_MAX,
    FARM_BONUS,
    GOLD_INTEREST,
    GOLD_PER_BOT,
    INTEREST_CAP,
    NEUTRAL_MAX,
    NEUTRAL_MIN,
    NEUTRAL_SPREAD,
    PRODUCTION,
)
from game.enums import BuildingKind, PlayerColor, TileKind
from game.schemas import Coord
from game.state import State, StateError

START = CAPITAL_GARRISON + PRODUCTION


@pytest.fixture
def game():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    bob = state.join("bob", PlayerColor.BLUE)
    state.start(alice.id)
    return state, alice, bob


def order(state, player, source, target, repeat=None):
    state.add_order(
        player.id, Coord(x=source[0], y=source[1]), Coord(x=target[0], y=target[1]), repeat
    )


def current(state):
    assert state.current is not None
    return state.current


def claim(state, player, x, y):
    tile = state.tile(Coord(x=x, y=y))
    tile.owner = player.id
    return tile


def test_capitals_and_first_production(game):
    state, alice, bob = game
    assert current(state).id == alice.id
    assert state.game.round == 1
    assert state.tile(Coord(x=0, y=0)).owner == alice.id
    assert state.tile(Coord(x=19, y=19)).owner == bob.id
    assert state.tile(Coord(x=0, y=0)).soldiers == START


def test_river_is_a_cross_and_starts_empty(game):
    state, _, _ = game
    assert state.tile(Coord(x=9, y=0)).kind == TileKind.WATER
    assert state.tile(Coord(x=0, y=9)).kind == TileKind.WATER
    assert state.tile(Coord(x=0, y=0)).kind == TileKind.LAND
    wet = [tile for row in state.game.tiles for tile in row if tile.kind == TileKind.WATER]
    assert all(tile.soldiers == 0 and tile.owner is None for tile in wet)


def test_transfer_moves_the_whole_stack(game):
    state, alice, _ = game
    target = state.tile(Coord(x=1, y=0))
    target.owner = alice.id
    target.soldiers = 0
    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)
    assert state.tile(Coord(x=0, y=0)).soldiers == 0
    assert target.soldiers == START


def test_walking_into_an_empty_tile(game):
    state, alice, _ = game
    target = state.tile(Coord(x=1, y=0))
    target.soldiers = 0
    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)
    assert target.owner == alice.id
    assert target.soldiers == START
    assert state.tile(Coord(x=0, y=0)).soldiers == 0


@pytest.mark.parametrize(
    "attacker, defender, roll, survivors, defenders_left, captured",
    [
        (10, 3, 0.0, 9, 0, True),
        (10, 30, 0.0, 7, 20, False),
        (10, 30, 0.99, 2, 27, False),
        (6, 3, 0.99, 4, 2, False),
        (1, 1, 0.0, 1, 0, True),
    ],
)
def test_exchange_math(game, monkeypatch, attacker, defender, roll, survivors, defenders_left, captured):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: roll)
    source = state.tile(Coord(x=0, y=0))
    target = state.tile(Coord(x=1, y=0))
    source.soldiers = attacker
    target.soldiers = defender
    target.owner = bob.id
    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)
    if captured:
        assert target.owner == alice.id
        assert target.soldiers == survivors
        assert source.soldiers == 0
    else:
        assert source.soldiers == survivors
        assert target.soldiers == defenders_left
        assert target.owner == bob.id


def test_loot_is_half_the_garrison_the_map_was_made_with(game, monkeypatch):
    state, alice, _ = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    neutral = state.tile(Coord(x=1, y=0))
    garrison = neutral.soldiers
    assert neutral.loot == garrison // 2

    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)

    survivors = START - START * garrison // (2 * (START + garrison))
    assert neutral.owner == alice.id
    assert neutral.soldiers == survivors + garrison // 2


def test_a_worn_down_tile_still_pays_in_full(game, monkeypatch):
    state, alice, _ = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    neutral = state.tile(Coord(x=1, y=0))
    garrison = neutral.soldiers
    neutral.soldiers = 20

    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)

    survivors = START - START * 20 // (2 * (START + 20))
    assert neutral.soldiers == survivors + garrison // 2


def test_loot_grows_with_the_ring(game, monkeypatch):
    state, alice, _ = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    cheap = state.tile(Coord(x=1, y=0))
    rich = state.tile(Coord(x=8, y=0))
    step = state.tile(Coord(x=7, y=0))
    step.owner = alice.id
    step.soldiers = 400

    assert cheap.loot < rich.loot
    cheap_garrison = cheap.soldiers
    rich_garrison = rich.soldiers

    order(state, alice, (0, 0), (1, 0))
    order(state, alice, (7, 0), (8, 0))
    state.end_turn(alice.id)

    def survivors(attacker, defender):
        return attacker - attacker * defender // (2 * (attacker + defender))

    assert cheap.owner == alice.id
    assert rich.owner == alice.id
    assert cheap.soldiers == survivors(START, cheap_garrison) + cheap_garrison // 2
    assert rich.soldiers == survivors(400, rich_garrison) + rich_garrison // 2


def test_round_production_reaches_everyone(game):
    state, alice, bob = game
    state.end_turn(alice.id)
    state.end_turn(bob.id)
    assert state.game.round == 2
    assert current(state).id == alice.id
    assert state.tile(Coord(x=0, y=0)).soldiers == START + PRODUCTION
    assert state.tile(Coord(x=19, y=19)).soldiers == START + PRODUCTION


def test_orders_are_validated(game):
    state, alice, bob = game
    with pytest.raises(StateError, match="do not own"):
        order(state, alice, (19, 19), (18, 19))
    with pytest.raises(StateError, match="not adjacent"):
        order(state, alice, (0, 0), (5, 5))
    state.tile(Coord(x=0, y=0)).soldiers = 5
    order(state, bob, (19, 19), (18, 19))
    assert [pending.target for pending in state.game.orders] == [Coord(x=18, y=19)]


def test_an_empty_tile_can_be_ordered_from(game):
    state, alice, _ = game
    state.tile(Coord(x=0, y=0)).soldiers = 0

    order(state, alice, (0, 0), (1, 0))

    assert state.game.orders[0].soldiers == 0


def test_a_standing_order_from_an_empty_tile_fills_in(game):
    state, alice, bob = game
    state.tile(Coord(x=0, y=0)).soldiers = 0
    state.tile(Coord(x=1, y=0)).soldiers = 0
    order(state, alice, (0, 0), (1, 0), repeat=True)

    state.end_turn(alice.id)
    state.end_turn(bob.id)
    state.end_turn(alice.id)

    assert state.tile(Coord(x=1, y=0)).owner == alice.id
    assert state.tile(Coord(x=1, y=0)).soldiers == PRODUCTION


def test_a_second_order_from_the_same_tile_replaces_the_first(game):
    state, alice, _ = game
    order(state, alice, (0, 0), (1, 0))
    order(state, alice, (0, 0), (0, 1))
    assert len(state.game.orders) == 1
    assert state.game.orders[0].target == Coord(x=0, y=1)


def test_orders_can_be_queued_while_waiting(game):
    state, alice, bob = game
    state.tile(Coord(x=19, y=19)).soldiers = 30
    empty = state.tile(Coord(x=18, y=19))
    empty.soldiers = 0
    order(state, bob, (19, 19), (18, 19))
    state.end_turn(alice.id)
    assert current(state).id == bob.id
    state.end_turn(bob.id)
    assert empty.owner == bob.id
    assert empty.soldiers == 30 + PRODUCTION


def test_a_plan_dies_with_its_tile(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    state.tile(Coord(x=19, y=19)).soldiers = 30
    march = state.tile(Coord(x=18, y=19))
    march.owner = alice.id
    march.soldiers = 100
    order(state, bob, (19, 19), (18, 19))
    order(state, alice, (18, 19), (19, 19))
    state.end_turn(alice.id)
    assert state.tile(Coord(x=19, y=19)).owner == alice.id
    assert state.game.orders == []
    assert "bob's plan at (19, 19) fell through" in state.game.log


def test_an_emptied_tile_goes_neutral(game):
    state, alice, _ = game
    shore = state.tile(Coord(x=1, y=0))
    shore.kind = TileKind.WATER
    shore.owner = alice.id
    shore.soldiers = 4
    keep = state.tile(Coord(x=1, y=1))
    keep.owner = alice.id
    keep.soldiers = 10
    order(state, alice, (1, 0), (1, 1))
    state.end_turn(alice.id)
    assert shore.owner is None
    assert shore.soldiers == 0
    assert keep.soldiers == 14


def test_a_tile_can_attack_and_be_reinforced_in_one_turn(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    middle = state.tile(Coord(x=1, y=0))
    middle.owner = alice.id
    middle.soldiers = 10
    target = state.tile(Coord(x=2, y=0))
    target.owner = bob.id
    target.soldiers = 5
    state.tile(Coord(x=0, y=0)).soldiers = 40

    order(state, alice, (1, 0), (2, 0))
    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)

    assert target.owner == alice.id
    assert middle.owner == alice.id
    assert middle.soldiers == 40
    assert state.tile(Coord(x=0, y=0)).soldiers == 0


def test_orders_can_be_cancelled(game):
    state, alice, _ = game
    order(state, alice, (0, 0), (1, 0))
    state.remove_order(alice.id, Coord(x=0, y=0))
    assert state.game.orders == []
    with pytest.raises(StateError, match="no order"):
        state.remove_order(alice.id, Coord(x=0, y=0))


def test_dropping_out_drops_uncommitted_orders(game):
    state, alice, bob = game
    target = state.tile(Coord(x=1, y=0))
    target.soldiers = 5
    order(state, alice, (0, 0), (1, 0))
    assert state.away(alice.id) is True
    state.drop(alice.id)
    assert state.game.orders == []
    assert current(state).id == bob.id
    assert target.soldiers == 5
    assert target.owner is None
    assert "dropped out, turn skipped" in state.game.log[-1]
    assert state.away(alice.id) is False


def test_an_away_player_is_skipped_and_can_resume(game):
    state, alice, bob = game
    state.away(bob.id)
    state.end_turn(alice.id)
    assert current(state).id == alice.id
    assert "bob's turn skipped, offline" in state.game.log
    state.resume(bob.id)
    state.end_turn(alice.id)
    assert current(state).id == bob.id


def test_water_takes_a_stack_without_loot(game, monkeypatch):
    state, alice, _ = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    water = state.tile(Coord(x=1, y=0))
    water.kind = TileKind.WATER
    water.owner = None
    water.soldiers = 0
    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)
    assert water.kind == TileKind.WATER
    assert water.owner == alice.id
    assert water.soldiers == START


def test_water_battle_pays_no_loot(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    water = state.tile(Coord(x=1, y=0))
    water.kind = TileKind.WATER
    water.owner = bob.id
    water.soldiers = 5
    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)
    attacker, defender = START, 5
    survivors = attacker - attacker * defender // (2 * (attacker + defender))
    assert water.owner == alice.id
    assert water.soldiers == survivors
    assert water.kind == TileKind.WATER


def test_water_produces_nothing(game):
    state, alice, bob = game
    sea = state.tile(Coord(x=1, y=0))
    sea.kind = TileKind.WATER
    sea.owner = alice.id
    sea.soldiers = 40
    state.end_turn(alice.id)
    state.end_turn(bob.id)
    assert sea.soldiers == 40
    assert state.tile(Coord(x=0, y=0)).soldiers == START + PRODUCTION


def test_elimination_clears_water_and_names_a_winner(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    state.tile(Coord(x=0, y=0)).soldiers = 1
    water = state.tile(Coord(x=9, y=5))
    water.owner = alice.id
    water.soldiers = 3
    coast = state.tile(Coord(x=1, y=0))
    coast.owner = bob.id
    coast.soldiers = 10
    state.end_turn(alice.id)
    order(state, bob, (1, 0), (0, 0))
    state.end_turn(bob.id)
    assert alice.eliminated
    assert state.game.winner == bob.id
    assert water.owner is None
    assert water.soldiers == 0


def test_a_stack_cannot_ride_through_the_queue(game):
    state, alice, _ = game
    behind = state.tile(Coord(x=0, y=0))
    middle = state.tile(Coord(x=1, y=0))
    ahead = state.tile(Coord(x=2, y=0))
    behind.soldiers = 10
    middle.owner = alice.id
    middle.soldiers = 5
    ahead.owner = None
    ahead.soldiers = 0

    order(state, alice, (0, 0), (1, 0))
    order(state, alice, (1, 0), (2, 0))
    state.end_turn(alice.id)

    assert ahead.owner == alice.id
    assert ahead.soldiers == 5
    assert middle.soldiers == 10
    assert behind.soldiers == 0


def test_a_reinforced_tile_attacks_with_its_own_count(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    behind = state.tile(Coord(x=0, y=0))
    middle = state.tile(Coord(x=1, y=0))
    target = state.tile(Coord(x=2, y=0))
    behind.soldiers = 10
    middle.owner = alice.id
    middle.soldiers = 5
    target.owner = bob.id
    target.soldiers = 3

    order(state, alice, (0, 0), (1, 0))
    order(state, alice, (1, 0), (2, 0))
    state.end_turn(alice.id)

    assert target.owner == alice.id
    assert target.soldiers == 5
    assert middle.soldiers == 10


def test_chat_keeps_a_capped_history(game):
    state, alice, bob = game
    state.chat(alice.id, "  hello   there  ")
    state.chat(bob.id, "hi")
    assert [(line.name, line.text) for line in state.game.chat] == [
        ("alice", "hello there"),
        ("bob", "hi"),
    ]
    for index in range(CHAT_LIMIT + 10):
        state.chat(alice.id, f"line {index}")
    assert len(state.game.chat) == CHAT_LIMIT
    assert state.game.chat[-1].text == f"line {CHAT_LIMIT + 9}"


def test_chat_rejects_empty_and_truncates_long(game):
    state, alice, _ = game
    with pytest.raises(StateError, match="say something"):
        state.chat(alice.id, "   \n  ")
    with pytest.raises(StateError, match="not in this game"):
        state.chat("nobody", "hello")
    state.chat(alice.id, "x" * (CHAT_MAX + 50))
    assert len(state.game.chat[-1].text) == CHAT_MAX


def test_a_small_board_keeps_the_two_wide_river():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    bob = state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, 10)
    assert state.game.size == 10
    assert len(state.game.tiles) == 10
    assert all(len(row) == 10 for row in state.game.tiles)
    assert [state.tile(Coord(x=x, y=0)).kind for x in range(10)] == [
        TileKind.LAND,
        TileKind.LAND,
        TileKind.LAND,
        TileKind.LAND,
        TileKind.WATER,
        TileKind.WATER,
        TileKind.LAND,
        TileKind.LAND,
        TileKind.LAND,
        TileKind.LAND,
    ]
    assert state.tile(Coord(x=0, y=4)).kind == TileKind.WATER
    assert state.tile(Coord(x=0, y=5)).kind == TileKind.WATER
    assert state.tile(Coord(x=0, y=0)).owner == alice.id
    assert state.tile(Coord(x=9, y=9)).owner == bob.id
    assert state.tile(Coord(x=9, y=0)).owner is None


def test_a_board_size_must_be_on_offer():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)
    with pytest.raises(StateError, match="not on offer"):
        state.start(alice.id, 13)
    assert not state.game.started


def test_the_map_can_be_laid_out_before_the_start(monkeypatch):
    flat(monkeypatch)
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)
    assert state.game.size == 20

    state.shape(alice.id, 10)

    assert state.game.size == 10
    assert len(state.game.tiles) == 10
    assert state.tile(Coord(x=2, y=0)).soldiers == (NEUTRAL_MIN + NEUTRAL_MAX) // 2


def test_the_game_starts_on_the_map_that_was_shown(monkeypatch):
    flat(monkeypatch)
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)
    state.shape(alice.id, 10)
    shown = [[tile.soldiers for tile in row] for row in state.game.tiles]

    state.start(alice.id, 10)

    assert state.game.size == 10
    assert state.tile(Coord(x=2, y=0)).soldiers == shown[0][2]
    assert state.tile(Coord(x=3, y=3)).soldiers == shown[3][3]


def test_rolling_the_map_again_deals_a_new_one(monkeypatch):
    rolls = iter(range(1000))

    def counting(floor, ceiling):
        return floor + (ceiling - floor) * (next(rolls) % 100) / 100

    monkeypatch.setattr(random, "uniform", counting)
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)
    before = [[tile.soldiers for tile in row] for row in state.game.tiles]

    state.shape(alice.id, 20)

    after = [[tile.soldiers for tile in row] for row in state.game.tiles]
    assert state.game.size == 20
    assert before != after


def test_the_map_is_fixed_once_the_game_is_on(game):
    state, alice, _ = game
    with pytest.raises(StateError, match="already in play"):
        state.shape(alice.id, 10)


def test_only_a_seated_player_can_lay_out_the_map():
    state = State()
    with pytest.raises(StateError, match="not in this game"):
        state.shape("nobody", 10)
    alice = state.join("alice", PlayerColor.RED)
    with pytest.raises(StateError, match="not on offer"):
        state.shape(alice.id, 13)
    assert state.game.size == 20


def test_four_players_take_the_four_corners():
    state = State()
    seats = [(0, 0), (19, 19), (19, 0), (0, 19)]
    players = [
        state.join(name, color)
        for name, color in (
            ("alice", PlayerColor.RED),
            ("bob", PlayerColor.BLUE),
            ("carol", PlayerColor.GREEN),
            ("dave", PlayerColor.YELLOW),
        )
    ]
    state.start(players[0].id)
    for player, (x, y) in zip(players, seats):
        assert state.tile(Coord(x=x, y=y)).owner == player.id
        assert state.tile(Coord(x=x, y=y)).soldiers == START


def test_join_rules():
    state = State()
    with pytest.raises(StateError, match="name is required"):
        state.join("   ", PlayerColor.RED)
    alice = state.join("alice", PlayerColor.RED)
    with pytest.raises(StateError, match="name is taken"):
        state.join("alice", PlayerColor.BLUE)
    with pytest.raises(StateError, match="color is taken"):
        state.join("bob", PlayerColor.RED)
    for name, color in (("bob", PlayerColor.BLUE), ("carol", PlayerColor.GREEN), ("dave", PlayerColor.YELLOW)):
        state.join(name, color)
    with pytest.raises(StateError, match="game is full"):
        state.join("erin", PlayerColor.PURPLE)
    state.start(alice.id)
    with pytest.raises(StateError, match="already started"):
        state.join("frank", PlayerColor.ORANGE)


def test_start_rules():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    with pytest.raises(StateError, match="at least two players"):
        state.start(alice.id)
    state.join("bob", PlayerColor.BLUE)
    with pytest.raises(StateError, match="not in this game"):
        state.start("nobody")
    assert not state.game.started


def test_a_turn_skips_the_eliminated():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    bob = state.join("bob", PlayerColor.BLUE)
    carol = state.join("carol", PlayerColor.GREEN)
    state.start(alice.id)
    for row in state.game.tiles:
        for tile in row:
            if tile.owner == bob.id:
                tile.owner = None
                tile.soldiers = 0
    state.end_turn(alice.id)
    assert bob.eliminated
    assert state.current is not None
    assert state.current.id == carol.id
    assert state.game.winner is None


def test_orders_must_stay_on_the_board(game):
    state, alice, _ = game
    with pytest.raises(StateError, match="off the board"):
        order(state, alice, (0, 0), (-1, 0))
    with pytest.raises(StateError, match="off the board"):
        order(state, alice, (0, 0), (0, -1))
    with pytest.raises(StateError, match="not adjacent"):
        order(state, alice, (0, 0), (0, 25))
    assert state.game.orders == []


def test_no_orders_before_the_game_starts():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    with pytest.raises(StateError, match="has not started"):
        state.add_order(alice.id, Coord(x=0, y=0), Coord(x=1, y=0))


def test_an_eliminated_player_cannot_order(game):
    state, _, bob = game
    bob.eliminated = True
    with pytest.raises(StateError, match="you are out"):
        order(state, bob, (19, 19), (18, 19))


def test_a_player_cannot_cancel_someone_elses_order(game):
    state, alice, bob = game
    order(state, alice, (0, 0), (1, 0))
    with pytest.raises(StateError, match="no order"):
        state.remove_order(bob.id, Coord(x=0, y=0))
    assert len(state.game.orders) == 1


def test_an_order_given_between_turns_picks_up_production(game):
    state, alice, bob = game
    empty = state.tile(Coord(x=1, y=0))
    empty.soldiers = 0
    state.end_turn(alice.id)
    order(state, alice, (0, 0), (1, 0))
    state.end_turn(bob.id)
    assert state.tile(Coord(x=0, y=0)).soldiers == START + PRODUCTION
    state.end_turn(alice.id)
    assert f"alice walked into (1, 0) with {START + PRODUCTION}" in state.game.log[-1]
    assert empty.soldiers == START + PRODUCTION
    assert state.tile(Coord(x=0, y=0)).soldiers == 0


def test_an_order_given_out_of_turn_picks_up_the_tile(game):
    state, alice, bob = game
    empty = state.tile(Coord(x=1, y=0))
    empty.soldiers = 0
    state.end_turn(alice.id)
    state.tile(Coord(x=0, y=0)).soldiers = 0
    order(state, alice, (0, 0), (1, 0))

    state.end_turn(bob.id)

    assert state.game.orders[0].soldiers == PRODUCTION


def test_two_stacks_can_take_one_tile_in_a_round(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    first = state.tile(Coord(x=1, y=0))
    first.owner = alice.id
    first.soldiers = 10
    second = state.tile(Coord(x=2, y=1))
    second.owner = alice.id
    second.soldiers = 10
    target = state.tile(Coord(x=2, y=0))
    target.owner = bob.id
    target.soldiers = 3
    order(state, alice, (1, 0), (2, 0))
    order(state, alice, (2, 1), (2, 0))
    state.end_turn(alice.id)
    assert target.owner == alice.id
    assert target.soldiers == 19
    assert first.soldiers == 0
    assert second.soldiers == 0


def test_an_emptied_land_tile_still_produces(game):
    state, alice, bob = game
    holding = state.tile(Coord(x=1, y=0))
    holding.owner = alice.id
    holding.soldiers = 0
    state.end_turn(alice.id)
    state.end_turn(bob.id)
    assert holding.owner == alice.id
    assert holding.soldiers == PRODUCTION


def test_chat_lines_are_stamped(game):
    state, alice, bob = game
    state.chat(alice.id, "hello")
    state.chat(bob.id, "hi")
    first, second = state.game.chat
    assert 0 < first.at <= second.at


def test_a_repeating_order_runs_every_round(game):
    state, alice, bob = game
    middle = state.tile(Coord(x=1, y=0))
    middle.owner = alice.id
    middle.soldiers = 5
    ahead = state.tile(Coord(x=2, y=0))
    ahead.owner = alice.id
    ahead.soldiers = 0

    order(state, alice, (0, 0), (1, 0), repeat=True)
    order(state, alice, (1, 0), (2, 0), repeat=True)
    state.end_turn(alice.id)

    assert state.tile(Coord(x=0, y=0)).soldiers == 0
    assert middle.soldiers == START
    assert ahead.soldiers == 5
    assert [pending.source for pending in state.game.orders] == [Coord(x=0, y=0), Coord(x=1, y=0)]

    state.end_turn(bob.id)
    assert middle.soldiers == START + PRODUCTION
    assert ahead.soldiers == 5 + PRODUCTION

    state.end_turn(alice.id)
    assert state.tile(Coord(x=0, y=0)).soldiers == 0
    assert middle.soldiers == PRODUCTION
    assert ahead.soldiers == START + PRODUCTION * 2 + 5


def test_a_repeating_order_picks_up_new_production(game):
    state, alice, bob = game
    pond = state.tile(Coord(x=1, y=0))
    pond.kind = TileKind.WATER
    pond.owner = None
    pond.soldiers = 0
    capital = state.tile(Coord(x=0, y=0))
    capital.soldiers = 1
    order(state, alice, (0, 0), (1, 0), repeat=True)

    state.end_turn(alice.id)
    assert capital.soldiers == 0
    assert pond.soldiers == 1

    state.end_turn(bob.id)
    assert capital.soldiers == PRODUCTION

    state.end_turn(alice.id)
    assert capital.soldiers == 0
    assert pond.soldiers == 1 + PRODUCTION


def test_a_repeating_order_survives_its_turn(game):
    state, alice, _ = game
    order(state, alice, (0, 0), (1, 0), repeat=True)
    state.end_turn(alice.id)
    assert len(state.game.orders) == 1
    assert state.game.orders[0].repeat is True
    assert state.game.orders[0].source == Coord(x=0, y=0)


def test_a_one_shot_order_is_spent(game):
    state, alice, _ = game
    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)
    assert state.game.orders == []


def test_a_repeating_order_dies_with_its_tile(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    keep = state.tile(Coord(x=1, y=1))
    keep.owner = alice.id
    keep.soldiers = 0
    source = state.tile(Coord(x=1, y=0))
    source.owner = alice.id
    source.soldiers = 5
    march = state.tile(Coord(x=2, y=0))
    march.owner = bob.id
    march.soldiers = 100

    order(state, alice, (1, 0), (1, 1), repeat=True)
    state.end_turn(alice.id)
    assert keep.soldiers == 5
    assert len(state.game.orders) == 1

    order(state, bob, (2, 0), (1, 0))
    state.end_turn(bob.id)
    assert state.tile(Coord(x=1, y=0)).owner == bob.id
    assert state.game.orders == []
    assert "alice's plan at (1, 0) fell through" in state.game.log


def test_a_repeat_can_be_turned_on_and_off(game):
    state, alice, _ = game
    order(state, alice, (0, 0), (1, 0))
    assert state.game.orders[0].repeat is False
    order(state, alice, (0, 0), (1, 0), repeat=True)
    assert len(state.game.orders) == 1
    assert state.game.orders[0].repeat is True
    order(state, alice, (0, 0), (1, 0))
    assert state.game.orders[0].repeat is True
    order(state, alice, (0, 0), (1, 0), repeat=False)
    assert state.game.orders[0].repeat is False


def test_a_move_stands_by_default(game):
    state, alice, _ = game
    state.tile(Coord(x=0, y=1)).owner = alice.id

    order(state, alice, (0, 0), (0, 1))

    assert state.game.orders[0].repeat is True


def test_an_attack_is_one_shot_by_default(game):
    state, alice, _ = game

    order(state, alice, (0, 0), (1, 0))

    assert state.game.orders[0].repeat is False


def test_a_redirect_takes_the_new_default(game):
    state, alice, _ = game
    state.tile(Coord(x=0, y=1)).owner = alice.id
    order(state, alice, (0, 0), (0, 1))
    assert state.game.orders[0].repeat is True

    order(state, alice, (0, 0), (1, 0))

    assert state.game.orders[0].repeat is False


def test_an_unchanged_order_keeps_its_flag(game):
    state, alice, _ = game
    state.tile(Coord(x=0, y=1)).owner = alice.id
    order(state, alice, (0, 0), (0, 1), repeat=False)

    order(state, alice, (0, 0), (0, 1))

    assert state.game.orders[0].repeat is False


def test_a_repeat_can_be_cancelled(game):
    state, alice, _ = game
    order(state, alice, (0, 0), (1, 0), repeat=True)
    state.remove_order(alice.id, Coord(x=0, y=0))
    assert state.game.orders == []


def flat(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda low, high: (low + high) / 2)


def test_garrisons_grow_towards_the_river(monkeypatch):
    flat(monkeypatch)
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, 10)

    assert state.tile(Coord(x=1, y=0)).soldiers == NEUTRAL_MIN
    assert state.tile(Coord(x=2, y=0)).soldiers == (NEUTRAL_MIN + NEUTRAL_MAX) // 2
    assert state.tile(Coord(x=3, y=0)).soldiers == NEUTRAL_MAX
    assert state.tile(Coord(x=1, y=0)).soldiers < state.tile(Coord(x=2, y=1)).soldiers
    assert state.tile(Coord(x=2, y=1)).soldiers < state.tile(Coord(x=3, y=3)).soldiers


def test_the_four_quadrants_match(monkeypatch):
    flat(monkeypatch)
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, 10)

    for step in range(1, 4):
        northwest = state.tile(Coord(x=step, y=0)).soldiers
        assert state.tile(Coord(x=9 - step, y=9)).soldiers == northwest
        assert state.tile(Coord(x=0, y=step)).soldiers == northwest
        assert state.tile(Coord(x=9, y=9 - step)).soldiers == northwest


def test_garrisons_stay_within_the_spread(monkeypatch):
    seen = []

    def watched(floor, ceiling):
        seen.append((floor, ceiling))
        return ceiling

    monkeypatch.setattr(random, "uniform", watched)
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, 10)

    assert seen
    for floor, ceiling in seen:
        assert ceiling <= NEUTRAL_MAX * (1 + NEUTRAL_SPREAD)
        assert floor >= NEUTRAL_MIN * (1 - NEUTRAL_SPREAD)
        assert floor < ceiling
    for row in state.game.tiles:
        for tile in row:
            assert tile.soldiers <= NEUTRAL_MAX * (1 + NEUTRAL_SPREAD)


def test_every_neutral_tile_holds_a_garrison(monkeypatch):
    flat(monkeypatch)
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, 20)

    for row in state.game.tiles:
        for tile in row:
            if tile.owner is not None:
                continue
            if tile.kind == TileKind.WATER:
                assert tile.soldiers == 0
                assert tile.loot == 0
            else:
                assert tile.soldiers >= NEUTRAL_MIN
                assert tile.loot == tile.soldiers // 2


def test_gold_comes_only_from_bot_land(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    monkeypatch.setattr(state_module, "GOLD_INTEREST", 0)
    assert alice.gold == 0

    bot = state.tile(Coord(x=1, y=0))
    bot.soldiers = 60
    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)
    assert bot.owner == alice.id
    assert alice.gold == GOLD_PER_BOT

    spoils = state.tile(Coord(x=18, y=19))
    spoils.owner = bob.id
    spoils.soldiers = 60
    springboard = state.tile(Coord(x=18, y=18))
    springboard.owner = alice.id
    springboard.soldiers = 300
    order(state, alice, (18, 18), (18, 19))
    state.end_turn(bob.id)
    state.end_turn(alice.id)
    assert spoils.owner == alice.id
    assert alice.gold == GOLD_PER_BOT


def test_water_pays_no_gold(game, monkeypatch):
    state, alice, _ = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    pond = state.tile(Coord(x=9, y=0))
    assert pond.kind == TileKind.WATER
    pond.owner = None
    pond.soldiers = 40
    state.tile(Coord(x=8, y=0)).owner = alice.id
    state.tile(Coord(x=8, y=0)).soldiers = 300
    order(state, alice, (8, 0), (9, 0))
    state.end_turn(alice.id)
    assert pond.owner == alice.id
    assert alice.gold == 0


def test_gold_earns_interest_every_round(game):
    state, alice, bob = game
    alice.gold = 1000

    state.end_turn(alice.id)
    state.end_turn(bob.id)

    assert alice.gold == 1000 + int(1000 * GOLD_INTEREST)


def test_interest_is_capped(game):
    state, alice, bob = game
    alice.gold = INTEREST_CAP * 100

    state.end_turn(alice.id)
    state.end_turn(bob.id)

    assert alice.gold == INTEREST_CAP * 100 + INTEREST_CAP


def test_a_broke_player_earns_nothing(game):
    state, alice, bob = game

    state.end_turn(alice.id)
    state.end_turn(bob.id)

    assert alice.gold == 0


def test_interest_pays_everyone_at_once(game):
    state, alice, bob = game
    alice.gold = 400
    bob.gold = 400

    state.end_turn(alice.id)
    state.end_turn(bob.id)

    assert (alice.gold, bob.gold) == (420, 420)


def test_a_farm_pays_extra_production(game):
    state, alice, bob = game
    before = claim(state, alice, 0, 1).soldiers
    alice.gold = BUILDING_COST
    state.build(alice.id, Coord(x=0, y=1), BuildingKind.FARM)
    assert state.tile(Coord(x=0, y=1)).buildings == [BuildingKind.FARM]
    state.end_turn(alice.id)
    state.end_turn(bob.id)
    assert state.tile(Coord(x=0, y=1)).soldiers == before + PRODUCTION + FARM_BONUS


def test_a_fort_doubles_the_defence(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    keep = state.tile(Coord(x=1, y=0))
    keep.owner = bob.id
    keep.soldiers = 100
    keep.buildings = [BuildingKind.FORT]
    state.tile(Coord(x=0, y=0)).soldiers = 100

    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)

    attacker, guard = 100, 200
    survivors = attacker - attacker * guard // (2 * (attacker + guard))
    assert keep.owner == alice.id
    assert keep.soldiers == survivors
    assert keep.buildings == []


def test_a_fort_still_loses_to_an_equal_stack_on_a_lucky_roll(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    keep = state.tile(Coord(x=1, y=0))
    keep.owner = bob.id
    keep.soldiers = 210
    keep.buildings = [BuildingKind.FORT]
    assert state.tile(Coord(x=0, y=0)).soldiers == 210

    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)

    assert keep.owner == alice.id


def test_a_fort_repels_a_weaker_attack_more_cheaply(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 1.0)
    keep = state.tile(Coord(x=1, y=0))
    keep.owner = bob.id
    keep.soldiers = 100
    keep.buildings = [BuildingKind.FORT]
    state.tile(Coord(x=0, y=0)).soldiers = 100

    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)

    assert keep.owner == bob.id
    assert state.tile(Coord(x=0, y=0)).soldiers == 100 - ceil(100 * 200 / 300)
    assert keep.soldiers == 100 - 200 // 6


def test_both_can_stand_on_one_tile(game):
    state, alice, _ = game
    claim(state, alice, 0, 1)
    alice.gold = BUILDING_COST * 2
    state.build(alice.id, Coord(x=0, y=1), BuildingKind.FARM)
    state.build(alice.id, Coord(x=0, y=1), BuildingKind.FORT)
    assert state.tile(Coord(x=0, y=1)).buildings == [BuildingKind.FARM, BuildingKind.FORT]
    assert alice.gold == 0


def test_building_is_paid_for_once(game):
    state, alice, _ = game
    alice.gold = BUILDING_COST * 3
    state.build(alice.id, Coord(x=0, y=0), BuildingKind.FARM)
    assert alice.gold == BUILDING_COST * 2
    with pytest.raises(StateError, match="already a farm"):
        state.build(alice.id, Coord(x=0, y=0), BuildingKind.FARM)
    assert alice.gold == BUILDING_COST * 2


def test_building_needs_the_gold(game):
    state, alice, _ = game
    claim(state, alice, 0, 1)
    alice.gold = BUILDING_COST - 1
    with pytest.raises(StateError, match=f"costs {BUILDING_COST}"):
        state.build(alice.id, Coord(x=0, y=1), BuildingKind.FARM)
    assert state.tile(Coord(x=0, y=1)).buildings == []


def test_building_rules(game):
    state, alice, bob = game
    alice.gold = BUILDING_COST * 3
    with pytest.raises(StateError, match="not yours"):
        state.build(alice.id, Coord(x=1, y=0), BuildingKind.FARM)
    pond = state.tile(Coord(x=9, y=0))
    pond.owner = alice.id
    pond.soldiers = 30
    with pytest.raises(StateError, match="on water"):
        state.build(alice.id, Coord(x=9, y=0), BuildingKind.FORT)
    with pytest.raises(StateError, match="not your turn"):
        state.build(bob.id, Coord(x=19, y=19), BuildingKind.FORT)
    state.end_turn(alice.id)
    with pytest.raises(StateError, match="not your turn"):
        state.build(alice.id, Coord(x=0, y=0), BuildingKind.FARM)


def test_a_captured_tile_loses_its_buildings(game, monkeypatch):
    state, alice, bob = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    farm = state.tile(Coord(x=1, y=0))
    farm.owner = bob.id
    farm.soldiers = 40
    farm.buildings = [BuildingKind.FARM, BuildingKind.FORT]
    state.tile(Coord(x=0, y=0)).soldiers = 200

    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)

    assert farm.owner == alice.id
    assert farm.buildings == []
    assert "razed a farm and a fort" in state.game.log[-1]


def test_a_wiped_player_loses_their_buildings(game):
    state, alice, bob = game
    capital = state.tile(Coord(x=19, y=19))
    capital.kind = TileKind.WATER
    capital.buildings = [BuildingKind.FARM]
    state.end_turn(alice.id)
    assert bob.eliminated
    assert capital.buildings == []

