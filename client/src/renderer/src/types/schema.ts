export enum TileType {
    PLAYER = 'player',
    BOT = 'bot'
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

export enum BotColor {
    GREY = "grey",
    BLACK = "black"
}

export enum CommandType {
    JOIN = 'JOIN',
    ATTACK = 'ATTACK'
}

export enum EventType {
    GRID_UPDATE = 'GRID_UPDATE',
    PLAYERS_UPDATE = 'PLAYERS_UPDATE',
    TILE_UPDATE = 'TILE_UPDATE'
}

export enum ResultType {
    CONNECT_SUCCESS = 'CONNECT_SUCCESS',
    JOIN_SUCCESS = 'JOIN_SUCCESS'
}

export interface Player {
    name: string
    color: PlayerColor
}

export interface Players {
    players: Player[]
}

export interface Tile {
    type: TileType
    color: PlayerColor | BotColor
}

export interface Grid {
    tiles: Tile[][]
}

export interface Game {
    grid: Grid
    players: Players
}

export interface JoinData {
    name: string
    color: PlayerColor
}

export interface AttackData {
    x: number
    y: number
}

// Helper types for WebSocket messages
export interface Command {
    type: CommandType
    data: JoinData | AttackData
}

export interface Event {
    type: EventType
    data: any // Dynamic based on type
}

export interface Result {
    type: ResultType
    data: any // Dynamic based on type
}

export interface TileUpdateData {
    x: number
    y: number
    tile: Tile
}
