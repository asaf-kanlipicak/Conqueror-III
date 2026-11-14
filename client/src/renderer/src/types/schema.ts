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
  CHAT = 'CHAT',
  END_TURN = 'END_TURN',
  RESET = 'RESET'
}

export enum MessageType {
  CONNECT_SUCCESS = 'CONNECT_SUCCESS',
  JOIN_SUCCESS = 'JOIN_SUCCESS',
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

export interface Move {
  source: Coord
  target: Coord
}

export interface PendingOrder extends Move {
  player: string
  soldiers: number
  repeat: boolean
}

export interface ChatLine {
  name: string
  text: string
  at: number
}

export interface Game {
  size: number
  tiles: Tile[][]
  players: Player[]
  orders: PendingOrder[]
  turn: number
  round: number
  started: boolean
  started_at: number | null
  winner: string | null
  log: string[]
  chat: ChatLine[]
}

export interface GameMessage {
  type: MessageType
  data?: unknown
}

export interface ErrorData {
  message: string
}
