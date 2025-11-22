from typing import List

class GameState:
    def __init__(self):
        self.grid: List[List[int]] = [[0 for _ in range(10)] for _ in range(10)]

    def toggle(self, x: int, y: int) -> int:
        self.grid[y][x] = 1 - self.grid[y][x]
        return self.grid[y][x]

    def get_state(self) -> List[List[int]]:
        return self.grid

game_state = GameState()
