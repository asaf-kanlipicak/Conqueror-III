import pytest

from game.constants import CAPITAL_GARRISON, PRODUCTION
from game.enums import BuildingKind, PlayerColor
from game.schemas import Coord
from game.state import State, StateError


@pytest.fixture
def finished():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    bob = state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, 10)
    state.game.winner = alice.id
    state.game.round = 42
    bob.eliminated = True
    bob.gold = 900
    bob.capital_lost = 2
    state.game.log.append("bob never retook their capital and is out")
    return state, alice, bob


def test_a_finished_game_can_be_started_again(finished):
    state, alice, bob = finished

    state.start(alice.id, 10)

    assert state.game.winner is None
    assert state.game.started
    assert state.game.round == 1
    assert state.game.log == ["the game is on, 2 players on a 10 by 10 board"]


def test_a_restart_gives_the_seats_back(finished):
    state, alice, bob = finished

    state.start(alice.id, 10)

    assert not bob.eliminated
    assert bob.gold == 0
    assert bob.capital_lost == 0
    assert state.tile(Coord(x=9, y=9)).owner == bob.id
    assert state.tile(Coord(x=0, y=0)).owner == alice.id


def test_a_restart_deals_a_fresh_board(finished):
    state, alice, bob = finished

    state.start(alice.id, 10)

    capital = state.tile(Coord(x=0, y=0))
    assert capital.soldiers == CAPITAL_GARRISON + PRODUCTION
    assert capital.buildings == [BuildingKind.FORT]
    assert sum(1 for row in state.game.tiles for tile in row if tile.owner) == 2


def test_a_restart_is_unpaused(finished):
    state, alice, bob = finished
    state.game.paused = True

    state.start(alice.id, 10)

    assert not state.game.paused


def test_a_restart_can_change_the_board_size(finished):
    state, alice, bob = finished

    state.start(alice.id, 20)

    assert state.game.size == 20
    assert len(state.game.tiles) == 20


def test_a_live_game_still_cannot_be_started():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, 10)

    with pytest.raises(StateError, match="already started"):
        state.start(alice.id, 10)


def test_a_finished_game_can_be_reshaped(finished):
    state, alice, bob = finished

    state.shape(alice.id, 20)

    assert state.game.size == 20
    assert not state.game.started
    assert state.game.winner is None
    assert not bob.eliminated


def test_a_live_game_still_cannot_be_reshaped():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, 10)

    with pytest.raises(StateError, match="already in play"):
        state.shape(alice.id, 20)


def test_a_restart_keeps_the_seats():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    bob = state.add_bot()
    state.start(alice.id, 10)
    state.game.winner = alice.id

    state.start(alice.id, 10)

    assert [player.id for player in state.game.players] == [alice.id, bob.id]
    assert state.game.players[1].bot is True
