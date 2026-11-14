import { describe, expect, it } from 'vitest'
import {
  boardSpan,
  clickTile,
  isAdjacent,
  isAttack,
  odds,
  orderArrow,
  orderCount,
  playerTotals,
  sameCoord,
  shownOrders,
  tileCenter
} from './board'
import { Game, PendingOrder, PlayerColor, TileKind, Tile } from '../types/schema'

function tile(owner: string | null, soldiers: number, kind: TileKind = TileKind.LAND): Tile {
  return { kind, owner, soldiers }
}

function sample(): Game {
  return {
    size: 2,
    tiles: [
      [tile('a', 5), tile(null, 2)],
      [tile('b', 3, TileKind.WATER), tile('a', 0)]
    ],
    players: [
      { id: 'a', name: 'alice', color: PlayerColor.RED, eliminated: false, online: true },
      { id: 'b', name: 'bob', color: PlayerColor.BLUE, eliminated: false, online: true }
    ],
    orders: [],
    turn: 0,
    round: 1,
    started: true,
    started_at: null,
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

  it('aims the head past the tail', () => {
    const arrow = orderArrow({ x: 0, y: 0 }, { x: 1, y: 0 })
    expect(arrow.head.startsWith(`M${arrow.x2},${arrow.y2}`)).toBe(true)
    expect(arrow.head.endsWith('Z')).toBe(true)
  })
})

describe('order counts', () => {
  function order(repeat: boolean, soldiers: number): PendingOrder {
    return { player: 'a', source: { x: 0, y: 0 }, target: { x: 1, y: 0 }, soldiers, repeat }
  }

  it('shows what a one-shot order was given, capped by the tile', () => {
    expect(orderCount(sample(), order(false, 0))).toBe(0)
    expect(orderCount(sample(), order(false, 9))).toBe(5)
  })

  it('shows the live garrison for a standing order', () => {
    expect(orderCount(sample(), order(true, 0))).toBe(5)
    expect(orderCount(sample(), order(true, 9))).toBe(5)
  })
})

describe('order filter', () => {
  const oneShot: PendingOrder = {
    player: 'a',
    source: { x: 0, y: 0 },
    target: { x: 1, y: 0 },
    soldiers: 5,
    repeat: false
  }
  const standing: PendingOrder = { ...oneShot, source: { x: 2, y: 0 }, repeat: true }

  it('leaves the list alone until asked to hide', () => {
    expect(shownOrders([oneShot, standing], false)).toEqual([oneShot, standing])
    expect(shownOrders([], false)).toEqual([])
  })

  it('drops the standing orders when hiding', () => {
    expect(shownOrders([oneShot, standing], true)).toEqual([oneShot])
    expect(shownOrders([standing], true)).toEqual([])
  })
})

describe('board clicks', () => {
  const corner = { x: 0, y: 0 }
  const next = { x: 1, y: 0 }
  const far = { x: 3, y: 3 }

  it('picks up one of your own tiles and ignores the rest', () => {
    expect(clickTile(null, corner, true, false)).toEqual({ kind: 'select', coord: corner })
    expect(clickTile(null, corner, false, false)).toEqual({ kind: 'select', coord: null })
  })

  it('orders into a neighbour, even one that has an order of its own', () => {
    expect(clickTile(corner, next, true, false)).toEqual({ kind: 'order', source: corner, target: next })
    expect(clickTile(corner, next, true, true)).toEqual({ kind: 'order', source: corner, target: next })
  })

  it('cancels a picked tile that has an order, and lets go of one that has not', () => {
    expect(clickTile(corner, corner, true, true)).toEqual({ kind: 'cancel', source: corner })
    expect(clickTile(corner, corner, true, false)).toEqual({ kind: 'select', coord: null })
  })

  it('moves the pick to another tile', () => {
    expect(clickTile(corner, far, true, false)).toEqual({ kind: 'select', coord: far })
    expect(clickTile(corner, far, false, false)).toEqual({ kind: 'select', coord: null })
  })
})
