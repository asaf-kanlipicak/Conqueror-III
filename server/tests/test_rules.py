import random

import pytest

from game.constants import CAPITAL_GARRISON, LOOT, PRODUCTION
from game.enums import PlayerColor, TileKind
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


def order(state, player, source, target):
    state.add_order(player.id, Coord(x=source[0], y=source[1]), Coord(x=target[0], y=target[1]))


def current(state):
    assert state.current is not None
    return state.current


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


def test_loot_only_comes_from_neutral_land(game, monkeypatch):
    state, alice, _ = game
    monkeypatch.setattr(random, "random", lambda: 0.0)
    neutral = state.tile(Coord(x=1, y=0))
    neutral.soldiers = 5
    order(state, alice, (0, 0), (1, 0))
    state.end_turn(alice.id)
    attacker, defender = START, 5
    survivors = attacker - attacker * defender // (2 * (attacker + defender))
    assert neutral.owner == alice.id
    assert neutral.soldiers == survivors + LOOT


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
    with pytest.raises(StateError, match="not your turn"):
        order(state, bob, (19, 19), (18, 19))
    with pytest.raises(StateError, match="do not own"):
        order(state, alice, (19, 19), (18, 19))
    with pytest.raises(StateError, match="not adjacent"):
        order(state, alice, (0, 0), (5, 5))
    with pytest.raises(StateError, match="no soldiers"):
        state.tile(Coord(x=0, y=0)).soldiers = 0
        order(state, alice, (0, 0), (1, 0))
    with pytest.raises(StateError, match="already has an order"):
        state.tile(Coord(x=0, y=0)).soldiers = 5
        order(state, alice, (0, 0), (1, 0))
        order(state, alice, (0, 0), (0, 1))


def test_orders_can_be_cancelled(game):
    state, alice, _ = game
    order(state, alice, (0, 0), (1, 0))
    state.remove_order(alice.id, Coord(x=0, y=0))
    assert state.orders == []
    with pytest.raises(StateError, match="no order"):
        state.remove_order(alice.id, Coord(x=0, y=0))


def test_disconnect_drops_uncommitted_orders(game):
    state, alice, bob = game
    target = state.tile(Coord(x=1, y=0))
    target.soldiers = 5
    order(state, alice, (0, 0), (1, 0))
    state.disconnect(alice.id)
    assert state.orders == []
    assert current(state).id == bob.id
    assert target.soldiers == 5
    assert target.owner is None
    assert "dropped out, turn skipped" in state.game.log[-1]
    before = len(state.game.log)
    state.disconnect(alice.id)
    assert len(state.game.log) == before


def test_offline_player_is_skipped_and_can_resume(game):
    state, alice, bob = game
    state.disconnect(bob.id)
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
