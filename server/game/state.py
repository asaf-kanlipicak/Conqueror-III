from game.constants import BOARD_SIZE
from game.enums import TileType
from game.models import Game, Grid, BotTile, Player, Tile, Players


class State:
    def __init__(self):
        self.game = Game(
            grid=Grid(
                tiles=[[BotTile() for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
            ),
            players=Players()
        )

    def add_player(self, player: Player) -> Players:
        self.game.players.players.append(player)
        return self.game.players

    def set_tile_owner(self, x: int, y: int, player: Player) -> Tile:
        tile = self.game.grid.tiles[y][x]
        tile.color = player.color
        tile.type = TileType.PLAYER
        return tile