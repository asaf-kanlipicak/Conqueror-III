import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client():
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
        assert game["tiles"][0][0]["owner"] == alice_id

        alice.send_json(
            {
                "type": "MOVE",
                "data": {"source": {"x": 0, "y": 0}, "target": {"x": 1, "y": 0}},
            }
        )
        assert receive_until(alice, "ORDER_ACCEPTED")["data"]["target"] == {"x": 1, "y": 0}

        alice.send_json({"type": "NONSENSE"})
        assert "made no sense" in receive_until(alice, "ERROR")["data"]["message"]

        alice.send_json(
            {"type": "MOVE", "data": {"source": {"x": 0, "y": 0}, "target": {"x": 5, "y": 5}}}
        )
        assert "not adjacent" in receive_until(alice, "ERROR")["data"]["message"]

        alice.send_json({"type": "END_TURN"})
        game = wait_game(alice, lambda state: state["turn"] == 1)
        assert game["players"][1]["name"] == "bob"
