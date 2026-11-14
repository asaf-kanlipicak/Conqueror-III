import { describe, expect, it } from 'vitest'
import { boardSpan, isAdjacent, isAttack, odds, orderArrow, playerTotals, sameCoord, tileCenter } from './board'
import { Game, PlayerColor, TileKind, Tile } from '../types/schema'

function tile(owner: string | null, soldiers: number, kind: TileKind = TileKind.LAND): Tile {
  return { kind, owner, soldiers }
}

function sample(): Game {
  return {
    tiles: [
      [tile('a', 5), tile(null, 2)],
      [tile('b', 3, TileKind.WATER), tile('a', 0)]
    ],
    players: [
      { id: 'a', name: 'alice', color: PlayerColor.RED, eliminated: false, online: true },
      { id: 'b', name: 'bob', color: PlayerColor.BLUE, eliminated: false, online: true }
    ],
    turn: 0,
    round: 1,
    started: true,
    winner: null,
    log: [],
    chat: []
  }
}

describe('player totals', () => {
  it('counts land only, but every soldier', () => {
    expect(playerTotals(sample(), 'a')).toEqual({ tiles: 2, soldiers: 5 })
    expect(playerTotals(sample(), 'b')).toEqual({ tiles: 0, soldiers: 3 })
    expect(playerTotals(sample(), 'nobody')).toEqual({ tiles: 0, soldiers: 0 })
  })
})

describe('adjacency', () => {
  it('is orthogonal only', () => {
    expect(isAdjacent({ x: 0, y: 0 }, { x: 1, y: 0 })).toBe(true)
    expect(isAdjacent({ x: 0, y: 0 }, { x: 0, y: 1 })).toBe(true)
    expect(isAdjacent({ x: 0, y: 0 }, { x: 1, y: 1 })).toBe(false)
    expect(isAdjacent({ x: 0, y: 0 }, { x: 0, y: 0 })).toBe(false)
  })

  it('compares coordinates by value', () => {
    expect(sameCoord({ x: 2, y: 3 }, { x: 2, y: 3 })).toBe(true)
    expect(sameCoord({ x: 2, y: 3 }, { x: 3, y: 2 })).toBe(false)
  })
})

describe('odds', () => {
  it('matches the server formula', () => {
    expect(odds(10, 10)).toBe(0.5)
    expect(odds(1, 3)).toBe(0.25)
    expect(odds(4, 0)).toBe(1)
    expect(odds(0, 0)).toBe(1)
  })
})

describe('order kind', () => {
  it('is an attack unless the target is mine', () => {
    const game = sample()
    expect(isAttack(game, { source: { x: 0, y: 0 }, target: { x: 1, y: 0 } }, 'a')).toBe(true)
    expect(isAttack(game, { source: { x: 1, y: 0 }, target: { x: 0, y: 0 } }, 'a')).toBe(false)
    expect(isAttack(game, { source: { x: 0, y: 0 }, target: { x: 1, y: 1 } }, null)).toBe(true)
  })
})

describe('geometry', () => {
  it('centres tiles inside the grid', () => {
    expect(tileCenter({ x: 0, y: 0 })).toEqual({ x: 21, y: 21 })
    expect(tileCenter({ x: 2, y: 1 })).toEqual({ x: 107, y: 64 })
  })

  it('sizes the board from its side', () => {
    expect(boardSpan(2)).toBe(85)
    expect(boardSpan(20)).toBe(859)
  })

  it('points an arrow from the source towards the target', () => {
    const arrow = orderArrow({ x: 0, y: 0 }, { x: 1, y: 0 })
    expect(arrow.y1).toBe(21)
    expect(arrow.y2).toBe(21)
    expect(arrow.x1).toBeGreaterThan(21)
    expect(arrow.x2).toBeGreaterThan(arrow.x1)
    expect(arrow.x2).toBeLessThan(64)

    const down = orderArrow({ x: 3, y: 3 }, { x: 3, y: 4 })
    expect(down.x1).toBe(down.x2)
    expect(down.y2).toBeGreaterThan(down.y1)
  })
})
