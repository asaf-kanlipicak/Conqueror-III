import pytest

from game.constants import PRODUCTION
from game.enums import BuildingKind, PlayerColor
from game.models import Tile
from game.schemas import Coord
from game.state import State, StateError


def board(size=10, garrison=100):
    return [[Tile(soldiers=garrison, loot=garrison // 2) for _ in range(size)] for _ in range(size)]


def table(size=10):
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    bob = state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, size)
    state.game.tiles = board(size)
    for player in (alice, bob):
        state.tile(player.capital).owner = player.id
    return state, alice, bob


def put(state, player, x, y, soldiers=100):
    tile = state.tile(Coord(x=x, y=y))
    tile.owner = player.id
    tile.soldiers = soldiers
    return tile


def bare(state, x, y):
    tile = state.tile(Coord(x=x, y=y))
    tile.owner = None
    tile.soldiers = 0
    tile.loot = 0
    return tile


def at(x, y):
    return Coord(x=x, y=y)


def legs(state, source):
    return [(order.target, order.soldiers) for order in state.game.orders if order.source == source]


def test_a_split_shares_the_tile_evenly():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    assert legs(state, at(5, 5)) == [(at(4, 5), 100), (at(6, 5), 100)]


def test_an_odd_split_leaves_the_remainder_home():
    state, alice, _ = table()
    put(state, alice, 5, 5, 201)
    bare(state, 4, 5)
    bare(state, 6, 5)

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    assert legs(state, at(5, 5)) == [(at(4, 5), 100), (at(6, 5), 100)]


def test_a_split_can_keep_a_share_home():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(5, 5)])
    assert legs(state, at(5, 5)) == [(at(4, 5), 100)]

    state.end_turn(alice.id)

    assert state.tile(at(4, 5)).soldiers == 100
    assert state.tile(at(5, 5)).soldiers == 100


def test_a_split_replaces_the_whole_tile_plan():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.add_order(alice.id, at(5, 5), at(5, 4))

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    assert legs(state, at(5, 5)) == [(at(4, 5), 100), (at(6, 5), 100)]


def test_a_split_lands_both_legs():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    state.end_turn(alice.id)

    assert state.tile(at(4, 5)).owner == alice.id
    assert state.tile(at(4, 5)).soldiers == 100
    assert state.tile(at(6, 5)).owner == alice.id
    assert state.tile(at(6, 5)).soldiers == 100
    assert state.tile(at(5, 5)).soldiers == 0


def test_a_split_can_hit_two_tiles_of_one_enemy():
    state, alice, bob = table()
    put(state, alice, 5, 5, 200)
    put(state, bob, 4, 5, 60)
    put(state, bob, 6, 5, 60)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    assert legs(state, at(5, 5)) == [(at(4, 5), 100), (at(6, 5), 100)]
    assert state.tile(at(4, 5)).owner == bob.id


def test_a_split_counts_a_repeat_once():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(4, 5)])

    assert legs(state, at(5, 5)) == [(at(4, 5), 200)]


def test_an_empty_split_clears_the_tile():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    state.add_order(alice.id, at(5, 5), at(4, 5))

    state.split_order(alice.id, at(5, 5), [])

    assert legs(state, at(5, 5)) == []


def test_a_split_attack_is_one_shot_by_default():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)

    state.split_order(alice.id, at(5, 5), [at(4, 5)])

    assert all(order.repeat is False for order in state.game.orders)


def test_a_split_of_moves_stands_by_default():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    put(state, alice, 4, 5, 0)
    put(state, alice, 6, 5, 0)

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    assert all(order.repeat for order in state.game.orders)


def test_a_mixed_split_takes_each_legs_default():
    state, alice, bob = table()
    put(state, alice, 5, 5, 200)
    put(state, alice, 4, 5, 0)
    put(state, bob, 6, 5, 100)

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    assert [(order.target, order.repeat) for order in state.game.orders] == [
        (at(4, 5), True),
        (at(6, 5), False),
    ]


def test_re_splitting_keeps_a_flag_you_set():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    put(state, alice, 4, 5, 0)
    state.split_order(alice.id, at(5, 5), [at(4, 5)])
    assert state.game.orders[0].repeat is True

    state.set_repeat(alice.id, at(5, 5), False)
    state.split_order(alice.id, at(5, 5), [at(4, 5)])

    assert state.game.orders[0].repeat is False


def test_a_split_needs_adjacent_targets():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)

    with pytest.raises(StateError, match="not adjacent"):
        state.split_order(alice.id, at(5, 5), [at(7, 5)])


def test_a_split_needs_a_tile_on_the_board():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)

    with pytest.raises(StateError, match="off the board"):
        state.split_order(alice.id, at(5, 5), [at(-1, 5)])


def test_a_split_needs_your_own_tile():
    state, alice, bob = table()
    put(state, bob, 5, 5, 200)

    with pytest.raises(StateError, match="do not own"):
        state.split_order(alice.id, at(5, 5), [at(4, 5)])


def test_an_empty_tile_can_still_be_split():
    state, alice, _ = table()
    put(state, alice, 5, 5, 0)
    bare(state, 4, 5)
    bare(state, 6, 5)

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    assert legs(state, at(5, 5)) == [(at(4, 5), 0), (at(6, 5), 0)]
    assert all(order.parts == 2 for order in state.game.orders)


def test_a_standing_split_of_an_empty_tile_fills_in():
    state, alice, bob = table()
    put(state, alice, 5, 5, 0)
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.end_turn(alice.id)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])
    state.set_repeat(alice.id, at(5, 5), True)

    state.end_turn(bob.id)
    state.end_turn(alice.id)

    assert state.tile(at(4, 5)).soldiers == 5
    assert state.tile(at(6, 5)).soldiers == 5


def test_a_split_needs_soldiers_for_every_leg():
    state, alice, _ = table()
    put(state, alice, 5, 5, 2)

    with pytest.raises(StateError, match="too few soldiers"):
        state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5), at(5, 4)])

    assert legs(state, at(5, 5)) == []


def test_a_refused_split_leaves_the_old_plan():
    state, alice, _ = table()
    put(state, alice, 5, 5, 2)
    bare(state, 4, 5)
    state.add_order(alice.id, at(5, 5), at(4, 5))

    with pytest.raises(StateError, match="too few soldiers"):
        state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5), at(5, 4)])

    assert legs(state, at(5, 5)) == [(at(4, 5), 2)]


def test_a_split_is_refused_before_the_game():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    bob = state.join("bob", PlayerColor.BLUE)

    with pytest.raises(StateError, match="has not started"):
        state.split_order(alice.id, at(0, 0), [at(1, 0)])


def test_a_cancel_takes_one_leg():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    state.remove_order(alice.id, at(5, 5), at(6, 5))

    assert legs(state, at(5, 5)) == [(at(4, 5), 100)]


def test_standing_one_leg_keeps_the_others():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    state.set_repeat(alice.id, at(5, 5), True)

    assert legs(state, at(5, 5)) == [(at(4, 5), 100), (at(6, 5), 100)]
    assert all(order.repeat for order in state.game.orders)


def test_a_split_stands_as_one():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    state.set_repeat(alice.id, at(5, 5), True)
    state.set_repeat(alice.id, at(5, 5), False)

    assert not any(order.repeat for order in state.game.orders)
    assert len(state.game.orders) == 2


def test_a_standing_split_is_redivided_each_round():
    state, alice, bob = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])
    state.set_repeat(alice.id, at(5, 5), True)
    state.end_turn(alice.id)

    state.tile(at(5, 5)).soldiers = 300
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.end_turn(bob.id)
    share = (300 + PRODUCTION) // 2
    state.end_turn(alice.id)

    assert state.tile(at(4, 5)).soldiers == share
    assert state.tile(at(6, 5)).soldiers == share


def test_a_standing_split_keeps_its_home_share():
    state, alice, bob = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(5, 5)])
    state.set_repeat(alice.id, at(5, 5), True)
    state.end_turn(alice.id)

    state.tile(at(5, 5)).soldiers = 300
    bare(state, 4, 5)
    state.end_turn(bob.id)
    share = (300 + PRODUCTION) // 2
    state.end_turn(alice.id)

    assert state.tile(at(4, 5)).soldiers == share
    assert state.tile(at(5, 5)).soldiers == share


def test_standing_a_tile_with_no_order_is_refused():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)

    with pytest.raises(StateError, match="no order"):
        state.set_repeat(alice.id, at(5, 5), True)


def test_a_cancel_without_a_target_takes_the_whole_tile():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    state.remove_order(alice.id, at(5, 5))

    assert legs(state, at(5, 5)) == []


def test_a_cancel_of_an_unknown_leg_is_refused():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    state.split_order(alice.id, at(5, 5), [at(4, 5)])

    with pytest.raises(StateError, match="no order"):
        state.remove_order(alice.id, at(5, 5), at(6, 5))


def test_a_split_only_touches_its_own_tile():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    put(state, alice, 5, 6, 100)
    bare(state, 4, 5)
    state.add_order(alice.id, at(5, 6), at(5, 7))

    state.split_order(alice.id, at(5, 5), [at(4, 5)])

    assert legs(state, at(5, 6)) == [(at(5, 7), 100)]


def test_a_split_can_still_be_ordered_by_left_click():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    state.add_order(alice.id, at(5, 5), at(5, 4))

    assert legs(state, at(5, 5)) == [(at(5, 4), 200)]


def test_a_split_never_carries_a_fort():
    state, alice, _ = table()
    tile = put(state, alice, 5, 5, 200)
    tile.buildings = [BuildingKind.FORT]
    bare(state, 4, 5)

    state.split_order(alice.id, at(5, 5), [at(4, 5)])

    assert legs(state, at(5, 5)) == [(at(4, 5), 200)]


def test_every_leg_carries_the_same_share():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    for coord in (at(4, 5), at(6, 5), at(5, 4)):
        bare(state, coord.x, coord.y)

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5), at(5, 4)])

    assert [order.soldiers for order in state.game.orders] == [66, 66, 66]


def test_all_legs_of_a_tile_agree_on_their_parts():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])
    state.set_repeat(alice.id, at(5, 5), True)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5), at(5, 4)])

    assert {order.parts for order in state.game.orders} == {3}


def test_the_legs_never_send_more_than_the_garrison():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    for coord in (at(4, 5), at(6, 5), at(5, 4)):
        bare(state, coord.x, coord.y)

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5), at(5, 4)])

    assert sum(order.soldiers for order in state.game.orders) <= state.tile(at(5, 5)).soldiers


def test_a_cancelled_leg_leaves_the_rest_dividing_by_the_group():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])

    state.remove_order(alice.id, at(5, 5), at(6, 5))

    assert legs(state, at(5, 5)) == [(at(4, 5), 100)]
    assert state.game.orders[0].parts == 2


def test_a_standing_split_is_rederived_from_the_live_garrison():
    state, alice, bob = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])
    state.set_repeat(alice.id, at(5, 5), True)
    state.end_turn(alice.id)

    state.tile(at(5, 5)).soldiers = 90
    bare(state, 4, 5)
    bare(state, 6, 5)
    state.end_turn(bob.id)
    state.end_turn(alice.id)

    assert state.tile(at(4, 5)).soldiers == 50
    assert state.tile(at(6, 5)).soldiers == 50


def test_a_leg_carries_its_share_not_the_garrison():
    state, alice, _ = table()
    put(state, alice, 5, 5, 200)
    bare(state, 4, 5)
    bare(state, 6, 5)

    state.split_order(alice.id, at(5, 5), [at(4, 5), at(6, 5)])
    state.set_repeat(alice.id, at(5, 5), True)

    live = state.tile(at(5, 5)).soldiers
    assert all(order.soldiers == live // order.parts for order in state.game.orders)
