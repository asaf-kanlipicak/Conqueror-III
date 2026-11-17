import asyncio
import random

from connection.manager import Manager
from game import dispatcher as dispatcher_module
from game.dispatcher import Command, CommandType, Dispatcher
from game.enums import PlayerColor
from game.schemas import Coord


def table(monkeypatch, grace: float = 0.0):
    monkeypatch.setattr(dispatcher_module, "RECONNECT_GRACE", grace)
    dispatcher = Dispatcher(Manager())
    alice = dispatcher.state.join("alice", PlayerColor.RED)
    dispatcher.state.join("bob", PlayerColor.BLUE)
    dispatcher.state.start(alice.id)
    return dispatcher, alice


def settle(dispatcher, coro):
    async def run():
        await coro
        if dispatcher.bots is not None:
            await dispatcher.bots

    asyncio.run(run())


def test_a_dropped_player_is_skipped_after_the_grace(monkeypatch):
    dispatcher, alice = table(monkeypatch)
    dispatcher.state.add_order(alice.id, Coord(x=0, y=0), Coord(x=1, y=0))

    asyncio.run(dispatcher.player_left(alice.id))

    assert not dispatcher.state.is_online(alice.id)
    assert dispatcher.state.game.orders == []
    assert dispatcher.state.current is not None
    assert dispatcher.state.current.name == "bob"


def test_a_player_who_comes_back_keeps_the_turn(monkeypatch):
    dispatcher, alice = table(monkeypatch, grace=0.05)

    async def drop_and_return():
        left = asyncio.create_task(dispatcher.player_left(alice.id))
        await asyncio.sleep(0.01)
        dispatcher.state.resume(alice.id)
        await left

    asyncio.run(drop_and_return())

    assert dispatcher.state.is_online(alice.id)
    assert dispatcher.state.current is not None
    assert dispatcher.state.current.id == alice.id


def test_a_second_drop_for_the_same_player_is_ignored(monkeypatch):
    dispatcher, alice = table(monkeypatch)
    asyncio.run(dispatcher.player_left(alice.id))
    before = len(dispatcher.state.game.log)

    asyncio.run(dispatcher.player_left(alice.id))

    assert len(dispatcher.state.game.log) == before


def test_a_bot_takes_its_turn(monkeypatch):
    monkeypatch.setattr(dispatcher_module, "BOT_PAUSE", 0)
    monkeypatch.setattr(random, "random", lambda: 0.0)
    dispatcher = Dispatcher(Manager())
    alice = dispatcher.state.join("alice", PlayerColor.RED)
    seated = dispatcher.state.add_bot()
    dispatcher.state.start(alice.id, 10)

    settle(dispatcher, dispatcher.dispatch_end_turn(alice.id, Command(type=CommandType.END_TURN)))

    assert dispatcher.state.current is not None
    assert dispatcher.state.current.id == alice.id
    assert dispatcher.state.game.round == 2
    owned = [
        tile for row in dispatcher.state.game.tiles for tile in row if tile.owner == seated.id
    ]
    assert len(owned) == 3
    assert any(order.player == seated.id for order in dispatcher.state.game.orders)


def test_a_bot_waits_for_its_turn(monkeypatch):
    monkeypatch.setattr(dispatcher_module, "BOT_PAUSE", 0)
    dispatcher = Dispatcher(Manager())
    alice = dispatcher.state.join("alice", PlayerColor.RED)
    dispatcher.state.add_bot()
    dispatcher.state.start(alice.id, 10)
    before = [[tile.owner for tile in row] for row in dispatcher.state.game.tiles]

    asyncio.run(dispatcher.dispatch_move(
        alice.id, Command(type=CommandType.MOVE, data={"source": {"x": 0, "y": 0}, "target": {"x": 1, "y": 0}})
    ))

    assert [[tile.owner for tile in row] for row in dispatcher.state.game.tiles] == before
    assert dispatcher.state.current is not None
    assert dispatcher.state.current.id == alice.id


def test_a_paused_bot_game_holds_still(monkeypatch):
    monkeypatch.setattr(dispatcher_module, "BOT_PAUSE", 0)
    dispatcher = Dispatcher(Manager())
    dispatcher.state.add_bot()
    dispatcher.state.add_bot()

    async def run():
        await dispatcher.dispatch_start(None, Command(type=CommandType.START, data={"size": 10}))
        await asyncio.sleep(0)
        await dispatcher.dispatch_pause(None, Command(type=CommandType.PAUSE, data={"paused": True}))
        frozen = dispatcher.state.game.round
        await asyncio.sleep(0.02)
        assert dispatcher.bots is None
        assert dispatcher.state.game.round == frozen
        await dispatcher.dispatch_pause(None, Command(type=CommandType.PAUSE, data={"paused": False}))
        await asyncio.sleep(0.02)
        assert dispatcher.state.game.round > frozen

    asyncio.run(run())


def test_an_all_bot_game_reaches_a_winner(monkeypatch):
    monkeypatch.setattr(dispatcher_module, "BOT_PAUSE", 0)
    dispatcher = Dispatcher(Manager())
    dispatcher.state.add_bot()
    dispatcher.state.add_bot()

    async def run():
        await dispatcher.dispatch_start(None, Command(type=CommandType.START, data={"size": 10}))
        assert dispatcher.bots is not None
        await dispatcher.bots

    asyncio.run(run())

    assert dispatcher.state.game.winner is not None


def test_a_running_bot_game_can_be_reset(monkeypatch):
    monkeypatch.setattr(dispatcher_module, "BOT_PAUSE", 0)
    dispatcher = Dispatcher(Manager())
    dispatcher.state.add_bot()
    dispatcher.state.add_bot()

    async def run():
        await dispatcher.dispatch_start(None, Command(type=CommandType.START, data={"size": 10}))
        await asyncio.sleep(0)
        await dispatcher.dispatch_reset(None, Command(type=CommandType.RESET))
        await asyncio.sleep(0)

    asyncio.run(run())

    assert not dispatcher.state.game.started
    assert dispatcher.state.game.players == []
    assert dispatcher.bots is None
