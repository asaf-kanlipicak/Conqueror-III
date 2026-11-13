import pytest

import main
from game.state import State


@pytest.fixture(autouse=True)
def fresh_game():
    main.dispatcher.state = State()
    yield
