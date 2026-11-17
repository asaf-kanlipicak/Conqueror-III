import pytest

from game.constants import CAPITAL_GARRISON, CAPITAL_GRACE, GOLD_PER_BOT, PRODUCTION
from game.enums import BuildingKind, PlayerColor, TileKind
from game.schemas import Coord
from game.state import State


def seated(names):
    state = State()
    players = [state.join(name, color) for name, color in names]
    state.start(players[0].id)
    return state, players


@pytest.fixture
def game():
    state, (alice, bob) = seated([("alice", PlayerColor.RED), ("bob", PlayerColor.BLUE)])
    return state, alice, bob


@pytest.fixture
def crowd():
    state, (alice, bob, carol) = seated(
        [("alice", PlayerColor.RED), ("bob", PlayerColor.BLUE), ("carol", PlayerColor.GREEN)]
    )
    return state, alice, bob, carol


def turns(state, count):
    for _ in range(count):
        if state.game.winner is not None:
            return
        current = state.current
        if current is None:
            return
        state.end_turn(current.id)


def rounds(state, count):
    turns(state, count * len(state.game.players))


def hold(state, player, x, y, soldiers=200):
    tile = state.tile(Coord(x=x, y=y))
    tile.owner = player.id
    tile.soldiers = soldiers
    return tile


def lose_capital(state, alice, bob):
    tile = state.tile(alice.capital)
    tile.owner = bob.id
    tile.buildings = []
    tile.soldiers = 50
    return tile


def test_each_capital_starts_forted(game):
    state, alice, bob = game

    for player in (alice, bob):
        tile = state.tile(player.capital)
        assert tile.owner == player.id
        assert tile.buildings == [BuildingKind.FORT]
        assert tile.soldiers == CAPITAL_GARRISON + PRODUCTION


def test_the_capital_sits_in_the_corner(game):
    state, alice, bob = game

    assert alice.capital == Coord(x=0, y=0)
    assert bob.capital == Coord(x=19, y=19)


def test_a_held_capital_never_starts_the_clock(game):
    state, alice, bob = game

    rounds(state, 4)

    assert alice.capital_lost == 0
    assert not alice.eliminated


def test_losing_the_capital_starts_the_clock(game):
    state, alice, bob = game
    hold(state, alice, 1, 0)
    lose_capital(state, alice, bob)

    rounds(state, 1)

    assert alice.capital_lost == 1
    assert not alice.eliminated


def test_the_clock_waits_for_the_round(game):
    state, alice, bob = game
    hold(state, alice, 1, 0)
    lose_capital(state, alice, bob)

    state.end_turn(alice.id)

    assert alice.capital_lost == 0

    state.end_turn(bob.id)

    assert alice.capital_lost == 1


def test_the_clock_counts_up_to_the_grace(game):
    state, alice, bob = game
    hold(state, alice, 1, 0)
    lose_capital(state, alice, bob)

    rounds(state, CAPITAL_GRACE - 1)

    assert alice.capital_lost == CAPITAL_GRACE - 1
    assert not alice.eliminated


def test_three_rounds_without_it_and_you_are_out(crowd):
    state, alice, bob, carol = crowd
    hold(state, alice, 1, 0)
    lose_capital(state, alice, bob)

    rounds(state, CAPITAL_GRACE)

    assert alice.eliminated
    assert "alice never retook their capital and is out" in state.game.log


def test_taking_it_back_resets_the_clock(crowd):
    state, alice, bob, carol = crowd
    hold(state, alice, 1, 0)
    capital = lose_capital(state, alice, bob)
    rounds(state, 2)
    assert alice.capital_lost == 2

    capital.owner = alice.id
    capital.soldiers = 300
    rounds(state, 1)

    assert alice.capital_lost == 0
    assert not alice.eliminated


def test_the_clock_restarts_if_it_is_lost_again(crowd):
    state, alice, bob, carol = crowd
    hold(state, alice, 1, 0)
    capital = lose_capital(state, alice, bob)
    rounds(state, 2)
    capital.owner = alice.id
    rounds(state, 1)
    assert alice.capital_lost == 0

    capital.owner = bob.id
    rounds(state, 1)

    assert alice.capital_lost == 1
    assert not alice.eliminated


def test_the_capital_fort_never_comes_back(crowd):
    state, alice, bob, carol = crowd
    hold(state, alice, 1, 0, 300)
    capital = lose_capital(state, alice, bob)
    rounds(state, 1)

    capital.owner = alice.id
    capital.soldiers = 300
    rounds(state, 2)

    assert capital.buildings == []


def test_the_collapse_hands_the_land_to_nobody(crowd):
    state, alice, bob, carol = crowd
    tile = hold(state, alice, 1, 0, 200)
    lose_capital(state, alice, bob)

    rounds(state, CAPITAL_GRACE)

    assert tile.owner is None


def test_a_collapsed_tile_carries_half_its_garrison_as_loot(crowd):
    state, alice, bob, carol = crowd
    tile = hold(state, alice, 1, 0, 200)
    lose_capital(state, alice, bob)

    rounds(state, CAPITAL_GRACE - 1)
    frozen = tile.soldiers
    rounds(state, 1)

    assert tile.loot == frozen // 2


def test_the_collapse_keeps_the_garrison(crowd):
    state, alice, bob, carol = crowd
    tile = hold(state, alice, 1, 0, 200)
    lose_capital(state, alice, bob)

    rounds(state, CAPITAL_GRACE - 1)
    frozen = tile.soldiers
    rounds(state, 1)

    assert tile.soldiers == frozen
    assert tile.soldiers > 0


def test_the_collapse_keeps_forts_and_razes_farms(crowd):
    state, alice, bob, carol = crowd
    tile = hold(state, alice, 1, 0, 200)
    tile.buildings = [BuildingKind.FARM, BuildingKind.FORT]
    lose_capital(state, alice, bob)

    rounds(state, CAPITAL_GRACE)

    assert tile.buildings == [BuildingKind.FORT]


def test_a_collapsed_territory_stops_producing(crowd):
    state, alice, bob, carol = crowd
    tile = hold(state, alice, 1, 0, 200)
    tile.buildings = [BuildingKind.FARM]
    lose_capital(state, alice, bob)

    rounds(state, CAPITAL_GRACE)
    frozen = tile.soldiers
    rounds(state, 1)

    assert tile.soldiers == frozen


def test_a_collapsed_tile_is_ordinary_neutral_land(crowd):
    state, alice, bob, carol = crowd
    tile = hold(state, alice, 1, 0, 200)
    lose_capital(state, alice, bob)

    rounds(state, CAPITAL_GRACE)

    assert tile.kind == TileKind.LAND
    assert tile.owner is None


def test_a_collapsed_tile_pays_gold_like_a_bot(crowd):
    state, alice, bob, carol = crowd
    tile = hold(state, alice, 18, 19, 200)
    lose_capital(state, alice, bob)
    rounds(state, CAPITAL_GRACE)
    tile.soldiers = 0
    bob.gold = 0

    for _ in range(len(state.game.players) * 2):
        if state.current is bob:
            break
        state.end_turn(state.current.id)
    state.add_order(bob.id, Coord(x=19, y=19), Coord(x=18, y=19))
    state.end_turn(bob.id)

    assert tile.owner == bob.id
    assert bob.gold == GOLD_PER_BOT


def test_the_last_player_standing_wins(game):
    state, alice, bob = game
    hold(state, alice, 1, 0)
    lose_capital(state, alice, bob)

    rounds(state, CAPITAL_GRACE)

    assert state.game.winner == bob.id


def test_a_collapsed_player_keeps_their_capital_coordinate(crowd):
    state, alice, bob, carol = crowd
    hold(state, alice, 1, 0)
    lose_capital(state, alice, bob)

    rounds(state, CAPITAL_GRACE)

    assert alice.capital == Coord(x=0, y=0)
    assert alice.capital_lost == 0


def test_a_capital_lost_with_no_land_left_is_a_plain_loss(game):
    state, alice, bob = game
    lose_capital(state, alice, bob)

    turns(state, 1)

    assert alice.eliminated
    assert "alice is out" in state.game.log
