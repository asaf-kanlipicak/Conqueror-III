import { BuildingKind, Coord, Game, Move, PendingOrder, Player, Tile, TileKind } from '../types/schema'

export const TILE_SIZE = 42
export const TILE_GAP = 1
export const BOARD_SIZES = [10, 20]
export const SEATS = 4
export const BUILDING_COST = 250
export const FORT_DEFENSE = 2
export const CAPITAL_GRACE = 3

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

export function guardOf(tile: Tile): number {
  return tile.buildings.includes(BuildingKind.FORT) ? tile.soldiers * FORT_DEFENSE : tile.soldiers
}

export function capitalOf(game: Game, coord: Coord): Player | undefined {
  return game.players.find((player) => player.capital !== null && sameCoord(player.capital, coord))
}

export function isAttack(game: Game, move: Move, owner: string | null): boolean {
  return game.tiles[move.target.y][move.target.x].owner !== owner
}

export function orderCount(game: Game, order: PendingOrder): number {
  const source = game.tiles[order.source.y][order.source.x]
  return order.repeat
    ? Math.min(Math.floor(source.soldiers / order.parts), source.soldiers)
    : Math.min(order.soldiers, source.soldiers)
}

export function shownOrders(orders: PendingOrder[], hideStanding: boolean): PendingOrder[] {
  return hideStanding ? orders.filter((order) => !order.repeat) : orders
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

export function clearsPlan(picked: Coord | null, coord: Coord, owned: boolean, legs: number): boolean {
  return owned && legs > 0 && picked !== null && sameCoord(picked, coord)
}

export function stepCursor(from: Coord, key: string, size: number): Coord | null {
  const steps: Record<string, Coord> = {
    ArrowLeft: { x: -1, y: 0 },
    ArrowRight: { x: 1, y: 0 },
    ArrowUp: { x: 0, y: -1 },
    ArrowDown: { x: 0, y: 1 }
  }
  const step = steps[key]
  if (!step) return null
  return {
    x: Math.min(size - 1, Math.max(0, from.x + step.x)),
    y: Math.min(size - 1, Math.max(0, from.y + step.y))
  }
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
  head: string
}

export function orderArrow(from: Coord, to: Coord): Arrow {
  const start = tileCenter(from)
  const end = tileCenter(to)
  const dx = end.x - start.x
  const dy = end.y - start.y
  const length = Math.hypot(dx, dy)
  const ux = dx / length
  const uy = dy / length
  const x2 = start.x + dx * 0.65
  const y2 = start.y + dy * 0.65
  const back = 9
  const half = 5
  const bx = x2 - ux * back
  const by = y2 - uy * back
  return {
    x1: start.x + dx * 0.28,
    y1: start.y + dy * 0.28,
    x2,
    y2,
    head: `M${x2},${y2} L${bx - uy * half},${by + ux * half} L${bx + uy * half},${by - ux * half} Z`
  }
}
