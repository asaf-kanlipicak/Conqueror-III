from typing import List

BOARD_SIZE = 20

class GameState:
    def __init__(self):
        self.grid: List[List[int]] = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    def toggle(self, x: int, y: int) -> int:
        self.grid[y][x] = 1 - self.grid[y][x]
        return self.grid[y][x]

    def get_state(self) -> List[List[int]]:
        return self.grid

game_state = GameState()
