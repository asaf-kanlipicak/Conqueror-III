from typing import List

from pydantic import BaseModel, Field

from game.enums import TileType, PlayerColor, BotColor


class Player(BaseModel):
    name: str = Field(..., max_length=20)
    color: PlayerColor

class Players(BaseModel):
    players: List[Player] = []


class Tile(BaseModel):
    type: TileType
    color: PlayerColor | BotColor

class BotTile(Tile):
    type: TileType = TileType.BOT
    color: BotColor = BotColor.GREY

class PlayerTile(Tile):
    type: TileType = TileType.PLAYER

class Grid(BaseModel):
    tiles: List[List[Tile]]

class Game(BaseModel):
    grid: Grid
    players: Players



