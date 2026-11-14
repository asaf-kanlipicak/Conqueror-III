import asyncio

from connection.manager import Manager
from game import dispatcher as dispatcher_module
from game.dispatcher import Dispatcher
from game.enums import PlayerColor
from game.schemas import Coord


def table(monkeypatch, grace: float = 0.0):
    monkeypatch.setattr(dispatcher_module, "RECONNECT_GRACE", grace)
    dispatcher = Dispatcher(Manager())
    alice = dispatcher.state.join("alice", PlayerColor.RED)
    dispatcher.state.join("bob", PlayerColor.BLUE)
    dispatcher.state.start(alice.id)
    return dispatcher, alice


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
