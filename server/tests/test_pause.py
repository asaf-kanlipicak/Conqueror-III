import pytest

from game.enums import PlayerColor
from game.schemas import Coord
from game.state import State, StateError


@pytest.fixture
def game():
    state = State()
    alice = state.join("alice", PlayerColor.RED)
    bob = state.join("bob", PlayerColor.BLUE)
    state.start(alice.id, 10)
    return state, alice, bob


def test_a_paused_game_refuses_to_end_a_turn(game):
    state, alice, bob = game
    state.pause(True)

    with pytest.raises(StateError, match="paused"):
        state.end_turn(alice.id)

    assert state.game.round == 1
    assert state.current is alice


def test_a_paused_game_does_not_skip_a_dropped_player(game):
    state, alice, bob = game
    state.pause(True)
    state.away(alice.id)

    state.drop(alice.id)

    assert state.current is alice
    assert "alice dropped out, waiting for the game to resume" in state.game.log


def test_a_resumed_game_skips_a_player_who_is_still_away(game):
    state, alice, bob = game
    state.pause(True)
    state.away(alice.id)
    state.drop(alice.id)

    state.pause(False)

    assert state.current is bob


def test_a_resumed_game_stays_with_a_player_who_is_back(game):
    state, alice, bob = game
    state.pause(True)
    state.away(alice.id)
    state.drop(alice.id)
    state.resume(alice.id)

    state.pause(False)

    assert state.current is alice


def test_pausing_is_logged_once(game):
    state, alice, bob = game

    state.pause(True)
    state.pause(True)

    assert state.game.log.count("the game is paused") == 1


def test_the_game_can_be_paused_and_resumed(game):
    state, alice, bob = game
    state.pause(True)
    assert state.game.paused

    state.pause(False)

    assert not state.game.paused
    assert "the game is back on" in state.game.log


def test_a_lobby_cannot_be_paused():
    state = State()
    state.join("alice", PlayerColor.RED)
    state.join("bob", PlayerColor.BLUE)

    with pytest.raises(StateError, match="has not started"):
        state.pause(True)


def test_a_finished_game_cannot_be_paused(game):
    state, alice, bob = game
    state.game.winner = alice.id

    with pytest.raises(StateError, match="is over"):
        state.pause(True)


def test_orders_can_still_be_planned_while_paused(game):
    state, alice, bob = game
    state.pause(True)

    state.add_order(alice.id, alice.capital, Coord(x=1, y=0))

    assert state.game.orders
    assert state.game.round == 1
