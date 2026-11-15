import pytest
from fastapi.testclient import TestClient

import main
from game import dispatcher as dispatcher_module
from game.constants import BOT_NAMES
from game.state import State


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(dispatcher_module, "RECONNECT_GRACE", 0)
    monkeypatch.setattr(dispatcher_module, "BOT_PAUSE", 0)
    main.dispatcher.state = State()
    main.sessions.clear()
    with TestClient(main.app) as test_client:
        yield test_client


def receive_until(socket, kind):
    while True:
        message = socket.receive_json()
        if message["type"] == kind:
            return message


def wait_game(socket, predicate):
    while True:
        message = socket.receive_json()
        if message["type"] == "GAME_UPDATE" and predicate(message["data"]):
            return message["data"]


def test_join_start_move_and_end_turn(client):
    with client.websocket_connect("/ws") as alice, client.websocket_connect("/ws") as bob:
        assert receive_until(alice, "CONNECT_SUCCESS")["data"]["started"] is False
        receive_until(bob, "CONNECT_SUCCESS")

        alice.send_json({"type": "JOIN", "data": {"name": "alice", "color": "red"}})
        alice_id = receive_until(alice, "JOIN_SUCCESS")["data"]["id"]

        bob.send_json({"type": "JOIN", "data": {"name": "bob", "color": "blue"}})
        receive_until(bob, "JOIN_SUCCESS")

        alice.send_json({"type": "START"})
        game = wait_game(alice, lambda state: state["started"])
        assert game["turn"] == 0
        assert game["size"] == 20
        assert game["started_at"] is not None
        assert game["tiles"][0][0]["owner"] == alice_id

        alice.send_json(
            {
                "type": "MOVE",
                "data": {"source": {"x": 0, "y": 0}, "target": {"x": 1, "y": 0}},
            }
        )
        game = wait_game(alice, lambda state: state["orders"])
        assert game["orders"][0]["target"] == {"x": 1, "y": 0}
        assert game["orders"][0]["player"] == alice_id
        assert game["orders"][0]["repeat"] is False

        alice.send_json({"type": "CANCEL", "data": {"source": {"x": 0, "y": 0}}})
        game = wait_game(alice, lambda state: not state["orders"])

        alice.send_json({"type": "NONSENSE"})
        assert "made no sense" in receive_until(alice, "ERROR")["data"]["message"]

        alice.send_json(
            {"type": "MOVE", "data": {"source": {"x": 0, "y": 0}, "target": {"x": 5, "y": 5}}}
        )
        assert "not adjacent" in receive_until(alice, "ERROR")["data"]["message"]

        alice.send_json({"type": "END_TURN"})
        game = wait_game(alice, lambda state: state["turn"] == 1)
        assert game["players"][1]["name"] == "bob"

        bob.send_json({"type": "CHAT", "data": {"text": "good luck"}})
        game = wait_game(alice, lambda state: state["chat"])
        assert [(line["name"], line["text"]) for line in game["chat"]] == [("bob", "good luck")]

        bob.send_json({"type": "CHAT", "data": {"text": "   "}})
        assert "say something" in receive_until(bob, "ERROR")["data"]["message"]


def test_a_small_board_can_be_chosen_at_the_start(client):
    with client.websocket_connect("/ws") as alice, client.websocket_connect("/ws") as bob:
        receive_until(alice, "CONNECT_SUCCESS")
        receive_until(bob, "CONNECT_SUCCESS")

        alice.send_json({"type": "JOIN", "data": {"name": "alice", "color": "red"}})
        receive_until(alice, "JOIN_SUCCESS")
        bob.send_json({"type": "JOIN", "data": {"name": "bob", "color": "blue"}})
        receive_until(bob, "JOIN_SUCCESS")

        alice.send_json({"type": "START", "data": {"size": 10}})
        game = wait_game(alice, lambda state: state["started"])
        assert game["size"] == 10
        assert len(game["tiles"]) == 10
        assert game["tiles"][9][9]["owner"] == game["players"][1]["id"]


def test_the_map_can_be_chosen_and_rolled_before_the_start(client):
    with client.websocket_connect("/ws") as alice, client.websocket_connect("/ws") as bob:
        receive_until(alice, "CONNECT_SUCCESS")
        receive_until(bob, "CONNECT_SUCCESS")
        alice.send_json({"type": "JOIN", "data": {"name": "alice", "color": "red"}})
        receive_until(alice, "JOIN_SUCCESS")
        bob.send_json({"type": "JOIN", "data": {"name": "bob", "color": "blue"}})
        receive_until(bob, "JOIN_SUCCESS")

        alice.send_json({"type": "MAP", "data": {"size": 10}})
        game = wait_game(bob, lambda state: state["size"] == 10)
        assert len(game["tiles"]) == 10
        assert game["started"] is False
        shown = game["tiles"]

        alice.send_json({"type": "MAP", "data": {"size": 10}})
        rolled = wait_game(bob, lambda state: state["tiles"] != shown)
        assert len(rolled["tiles"]) == 10

        alice.send_json({"type": "START", "data": {"size": 10}})
        game = wait_game(alice, lambda state: state["started"])
        assert game["size"] == 10

        alice.send_json({"type": "MAP", "data": {"size": 20}})
        assert "already in play" in receive_until(alice, "ERROR")["data"]["message"]


def test_a_player_takes_their_seat_back(client):
    with client.websocket_connect("/ws") as alice:
        receive_until(alice, "CONNECT_SUCCESS")
        alice.send_json({"type": "JOIN", "data": {"name": "alice", "color": "red"}})
        player_id = receive_until(alice, "JOIN_SUCCESS")["data"]["id"]

        with client.websocket_connect("/ws") as again:
            receive_until(again, "CONNECT_SUCCESS")
            again.send_json({"type": "RESUME", "data": {"player_id": player_id}})
            resumed = receive_until(again, "JOIN_SUCCESS")["data"]
            assert resumed["id"] == player_id
            assert resumed["online"] is True
            assert resumed["name"] == "alice"


def test_a_standing_order_comes_back_every_round(client):
    with client.websocket_connect("/ws") as alice, client.websocket_connect("/ws") as bob:
        receive_until(alice, "CONNECT_SUCCESS")
        receive_until(bob, "CONNECT_SUCCESS")
        alice.send_json({"type": "JOIN", "data": {"name": "alice", "color": "red"}})
        receive_until(alice, "JOIN_SUCCESS")
        bob.send_json({"type": "JOIN", "data": {"name": "bob", "color": "blue"}})
        receive_until(bob, "JOIN_SUCCESS")
        alice.send_json({"type": "START"})
        wait_game(alice, lambda state: state["started"])

        alice.send_json(
            {
                "type": "MOVE",
                "data": {"source": {"x": 0, "y": 0}, "target": {"x": 1, "y": 0}, "repeat": True},
            }
        )
        game = wait_game(alice, lambda state: state["orders"])
        assert game["orders"][0]["repeat"] is True

        alice.send_json({"type": "END_TURN"})
        game = wait_game(alice, lambda state: state["turn"] == 1)
        assert [(order["source"], order["repeat"]) for order in game["orders"]] == [
            ({"x": 0, "y": 0}, True)
        ]

        alice.send_json({"type": "CANCEL", "data": {"source": {"x": 0, "y": 0}}})
        game = wait_game(bob, lambda state: not state["orders"])
        assert game["orders"] == []


def test_a_farm_can_be_built_over_the_socket(client):
    with client.websocket_connect("/ws") as alice, client.websocket_connect("/ws") as bob:
        receive_until(alice, "CONNECT_SUCCESS")
        receive_until(bob, "CONNECT_SUCCESS")
        alice.send_json({"type": "JOIN", "data": {"name": "alice", "color": "red"}})
        receive_until(alice, "JOIN_SUCCESS")
        bob.send_json({"type": "JOIN", "data": {"name": "bob", "color": "blue"}})
        receive_until(bob, "JOIN_SUCCESS")
        alice.send_json({"type": "START"})
        wait_game(alice, lambda state: state["started"])

        alice.send_json(
            {"type": "BUILD", "data": {"source": {"x": 0, "y": 0}, "building": "farm"}}
        )
        assert "costs 250" in receive_until(alice, "ERROR")["data"]["message"]

        alice.send_json(
            {"type": "BUILD", "data": {"source": {"x": 0, "y": 0}, "building": "tower"}}
        )
        assert "made no sense" in receive_until(alice, "ERROR")["data"]["message"]

        bob.send_json(
            {"type": "BUILD", "data": {"source": {"x": 19, "y": 19}, "building": "fort"}}
        )
        assert "not your turn" in receive_until(bob, "ERROR")["data"]["message"]


def test_a_bot_is_seated_and_plays_its_turn(client):
    with client.websocket_connect("/ws") as alice:
        receive_until(alice, "CONNECT_SUCCESS")
        alice.send_json({"type": "JOIN", "data": {"name": "alice", "color": "red"}})
        receive_until(alice, "JOIN_SUCCESS")

        alice.send_json({"type": "BOT"})
        game = wait_game(alice, lambda state: len(state["players"]) == 2)
        assert game["players"][1]["bot"] is True
        assert game["players"][1]["name"] in BOT_NAMES

        alice.send_json({"type": "START", "data": {"size": 10}})
        wait_game(alice, lambda state: state["started"])

        alice.send_json({"type": "END_TURN"})
        game = wait_game(alice, lambda state: state["round"] == 2 and state["turn"] == 0)
        assert game["players"][1]["bot"] is True
        assert any(order["player"] == game["players"][1]["id"] for order in game["orders"])


def test_reset_clears_the_table(client):
    with client.websocket_connect("/ws") as alice, client.websocket_connect("/ws") as bob:
        receive_until(alice, "CONNECT_SUCCESS")
        receive_until(bob, "CONNECT_SUCCESS")
        alice.send_json({"type": "JOIN", "data": {"name": "alice", "color": "red"}})
        receive_until(alice, "JOIN_SUCCESS")
        bob.send_json({"type": "JOIN", "data": {"name": "bob", "color": "blue"}})
        receive_until(bob, "JOIN_SUCCESS")
        alice.send_json({"type": "START"})
        wait_game(alice, lambda state: state["started"])

        alice.send_json({"type": "RESET"})
        game = wait_game(alice, lambda state: not state["players"])
        assert game["started"] is False
        assert game["started_at"] is None
        assert game["orders"] == []
        assert len(game["tiles"]) == 20
