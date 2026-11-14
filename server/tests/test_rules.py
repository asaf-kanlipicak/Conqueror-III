import random

import pytest

from game.constants import CAPITAL_GARRISON, CHAT_LIMIT, CHAT_MAX, LOOT, PRODUCTION
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


def order(state, player, source, target, repeat=None):
    state.add_order(
        player.id, Coord(x=source[0], y=source[1]), Coord(x=target[0], y=target[1]), repeat
    )


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
    with pytest.raises(StateError, match="do not own"):
        order(state, alice, (19, 19), (18, 19))
    with pytest.raises(StateError, match="not adjacent"):
        order(state, alice, (0, 0), (5, 5))
    with pytest.raises(StateError, match="no soldiers"):
        state.tile(Coord(x=0, y=0)).soldiers = 0
        order(state, alice, (0, 0), (1, 0))
    state.tile(Coord(x=0, y=0)).soldiers = 5
    order(state, bob, (19, 19), (18, 19))
    assert [pending.target for pending in state.game.orders] == [Coord(x=18, y=19)]


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


def test_a_snapshot_ignores_production(game):
    state, alice, bob = game
    empty = state.tile(Coord(x=1, y=0))
    empty.soldiers = 0
    state.end_turn(alice.id)
    order(state, alice, (0, 0), (1, 0))
    state.end_turn(bob.id)
    assert state.tile(Coord(x=0, y=0)).soldiers == START + PRODUCTION
    state.end_turn(alice.id)
    assert "alice walked into (1, 0) with 210" in state.game.log
    assert empty.soldiers == 210
    assert state.tile(Coord(x=0, y=0)).soldiers == PRODUCTION


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
    order(state, alice, (0, 0), (0, 1))
    assert state.game.orders[0].repeat is True
    order(state, alice, (0, 0), (0, 1), repeat=False)
    assert state.game.orders[0].repeat is False


def test_a_repeat_can_be_cancelled(game):
    state, alice, _ = game
    order(state, alice, (0, 0), (1, 0), repeat=True)
    state.remove_order(alice.id, Coord(x=0, y=0))
    assert state.game.orders == []
