export enum TileKind {
  LAND = 'land',
  WATER = 'water'
}

export enum PlayerColor {
  RED = 'red',
  GREEN = 'green',
  BLUE = 'blue',
  YELLOW = 'yellow',
  ORANGE = 'orange',
  TURQUOISE = 'turquoise',
  PURPLE = 'purple',
  WHITE = 'white'
}

export enum CommandType {
  JOIN = 'JOIN',
  RESUME = 'RESUME',
  START = 'START',
  MOVE = 'MOVE',
  CANCEL = 'CANCEL',
  END_TURN = 'END_TURN',
  RESET = 'RESET'
}

export enum MessageType {
  CONNECT_SUCCESS = 'CONNECT_SUCCESS',
  JOIN_SUCCESS = 'JOIN_SUCCESS',
  ORDER_ACCEPTED = 'ORDER_ACCEPTED',
  ORDER_CANCELLED = 'ORDER_CANCELLED',
  ERROR = 'ERROR',
  GAME_UPDATE = 'GAME_UPDATE'
}

export interface Coord {
  x: number
  y: number
}

export interface Tile {
  kind: TileKind
  owner: string | null
  soldiers: number
}

export interface Player {
  id: string
  name: string
  color: PlayerColor
  eliminated: boolean
  online: boolean
}

export interface Game {
  tiles: Tile[][]
  players: Player[]
  turn: number
  round: number
  started: boolean
  winner: string | null
  log: string[]
}

export interface Move {
  source: Coord
  target: Coord
}

export interface GameMessage {
  type: MessageType
  data?: unknown
}

export interface ErrorData {
  message: string
}
