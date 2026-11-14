import { Coord, Game, Move, TileKind } from '../types/schema'

export const TILE_SIZE = 42
export const TILE_GAP = 1

export interface Totals {
  tiles: number
  soldiers: number
}

export function sameCoord(a: Coord, b: Coord): boolean {
  return a.x === b.x && a.y === b.y
}

export function isAdjacent(a: Coord, b: Coord): boolean {
  return Math.abs(a.x - b.x) + Math.abs(a.y - b.y) === 1
}

export function odds(attacker: number, defender: number): number {
  const total = attacker + defender
  return total === 0 ? 1 : attacker / total
}

export function isAttack(game: Game, move: Move, myId: string | null): boolean {
  return game.tiles[move.target.y][move.target.x].owner !== myId
}

export function playerTotals(game: Game, playerId: string): Totals {
  let tiles = 0
  let soldiers = 0
  for (const row of game.tiles) {
    for (const tile of row) {
      if (tile.owner !== playerId) continue
      soldiers += tile.soldiers
      if (tile.kind === TileKind.LAND) tiles += 1
    }
  }
  return { tiles, soldiers }
}

export function boardSpan(side: number): number {
  return side * TILE_SIZE + (side - 1) * TILE_GAP
}

export function tileCenter(coord: Coord): { x: number; y: number } {
  const step = TILE_SIZE + TILE_GAP
  return { x: coord.x * step + TILE_SIZE / 2, y: coord.y * step + TILE_SIZE / 2 }
}

export interface Arrow {
  x1: number
  y1: number
  x2: number
  y2: number
}

export function orderArrow(from: Coord, to: Coord): Arrow {
  const start = tileCenter(from)
  const end = tileCenter(to)
  const dx = end.x - start.x
  const dy = end.y - start.y
  return {
    x1: start.x + dx * 0.28,
    y1: start.y + dy * 0.28,
    x2: start.x + dx * 0.65,
    y2: start.y + dy * 0.65
  }
}
