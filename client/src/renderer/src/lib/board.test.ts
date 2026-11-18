import { describe, expect, it } from 'vitest'
import {
  boardSpan,
  capitalOf,
  clearsPlan,
  guardOf,
  isAdjacent,
  isAttack,
  odds,
  orderArrow,
  orderCount,
  playerTotals,
  sameCoord,
  shownOrders,
  stepCursor,
  tileCenter
} from './board'
import { BuildingKind, Game, PendingOrder, PlayerColor, TileKind, Tile } from '../types/schema'

function tile(owner: string | null, soldiers: number, kind: TileKind = TileKind.LAND): Tile {
  return { kind, owner, soldiers, loot: 0, buildings: [] }
}

function sample(): Game {
  return {
    size: 2,
    tiles: [
      [tile('a', 5), tile(null, 2)],
      [tile('b', 3, TileKind.WATER), tile('a', 0)]
    ],
    players: [
      {
        id: 'a',
        name: 'alice',
        color: PlayerColor.RED,
        eliminated: false,
        online: true,
        bot: false,
        gold: 0,
        capital: { x: 0, y: 0 },
        capital_lost: 0
      },
      {
        id: 'b',
        name: 'bob',
        color: PlayerColor.BLUE,
        eliminated: false,
        online: true,
        bot: false,
        gold: 0,
        capital: { x: 1, y: 1 },
        capital_lost: 0
      }
    ],
    orders: [],
    turn: 0,
    round: 1,
    started: true,
    paused: false,
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

describe('forts', () => {
  it('doubles the garrison a fort is holding', () => {
    const plain = tile('a', 100)
    const fort = { ...tile('a', 100), buildings: [BuildingKind.FORT] }
    expect(guardOf(plain)).toBe(100)
    expect(guardOf(fort)).toBe(200)
  })

  it('gives an equal stack a third of a chance', () => {
    const fort = { ...tile('a', 100), buildings: [BuildingKind.FORT] }
    expect(odds(100, guardOf(fort))).toBeCloseTo(1 / 3)
    expect(odds(100, guardOf(tile('a', 100)))).toBeCloseTo(1 / 2)
  })

  it('still counts a farm as no defence', () => {
    expect(guardOf({ ...tile('a', 100), buildings: [BuildingKind.FARM] })).toBe(100)
  })
})

describe('order counts', () => {
  function order(repeat: boolean, soldiers: number, parts = 1): PendingOrder {
    return { player: 'a', source: { x: 0, y: 0 }, target: { x: 1, y: 0 }, soldiers, repeat, parts }
  }

  function holding(soldiers: number): Game {
    const game = sample()
    game.tiles[0][0].soldiers = soldiers
    return game
  }

  it('shows what a one-shot order was given, capped by the tile', () => {
    expect(orderCount(sample(), order(false, 0))).toBe(0)
    expect(orderCount(sample(), order(false, 9))).toBe(5)
  })

  it('shows the live garrison for a standing order', () => {
    expect(orderCount(sample(), order(true, 0))).toBe(5)
    expect(orderCount(sample(), order(true, 9))).toBe(5)
  })

  it('shows a standing split as its share of the live garrison', () => {
    expect(orderCount(holding(200), order(true, 0, 2))).toBe(100)
    expect(orderCount(holding(300), order(true, 0, 3))).toBe(100)
  })

  it('rounds a share down, the way the server divides', () => {
    expect(orderCount(holding(200), order(true, 0, 3))).toBe(66)
    expect(orderCount(holding(10), order(true, 0, 4))).toBe(2)
  })

  it('ignores parts on a one-shot, which already carries its share', () => {
    expect(orderCount(holding(200), order(false, 100, 2))).toBe(100)
  })

  it('never promises more than the tile holds', () => {
    expect(orderCount(holding(4), order(true, 0, 3))).toBe(1)
    expect(orderCount(holding(0), order(true, 0, 2))).toBe(0)
  })

  it('divides one garrison across its legs without inventing soldiers', () => {
    const game = holding(200)
    const legs = [order(true, 0, 3), order(true, 0, 3), order(true, 0, 3)]
    const shown = legs.reduce((sum, leg) => sum + orderCount(game, leg), 0)

    expect(shown).toBe(198)
    expect(shown).toBeLessThanOrEqual(200)
  })
})

describe('order filter', () => {
  const oneShot: PendingOrder = {
    player: 'a',
    source: { x: 0, y: 0 },
    target: { x: 1, y: 0 },
    soldiers: 5,
    repeat: false,
    parts: 1
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

describe('clearing a plan', () => {
  const corner = { x: 0, y: 0 }
  const next = { x: 1, y: 0 }

  it('clears the tile that is already picked', () => {
    expect(clearsPlan(corner, corner, true, 3)).toBe(true)
    expect(clearsPlan(corner, corner, true, 1)).toBe(true)
  })

  it('leaves every other tile alone', () => {
    expect(clearsPlan(corner, next, true, 3)).toBe(false)
    expect(clearsPlan(null, corner, true, 3)).toBe(false)
  })

  it('only clears a tile that has orders', () => {
    expect(clearsPlan(corner, corner, true, 0)).toBe(false)
  })

  it('never clears a tile you do not own', () => {
    expect(clearsPlan(corner, corner, false, 3)).toBe(false)
  })
})

describe('cursor keys', () => {
  const middle = { x: 2, y: 2 }

  it('walks one tile at a time', () => {
    expect(stepCursor(middle, 'ArrowLeft', 5)).toEqual({ x: 1, y: 2 })
    expect(stepCursor(middle, 'ArrowRight', 5)).toEqual({ x: 3, y: 2 })
    expect(stepCursor(middle, 'ArrowUp', 5)).toEqual({ x: 2, y: 1 })
    expect(stepCursor(middle, 'ArrowDown', 5)).toEqual({ x: 2, y: 3 })
  })

  it('stops at the edges instead of wrapping', () => {
    expect(stepCursor({ x: 0, y: 0 }, 'ArrowLeft', 5)).toEqual({ x: 0, y: 0 })
    expect(stepCursor({ x: 0, y: 0 }, 'ArrowUp', 5)).toEqual({ x: 0, y: 0 })
    expect(stepCursor({ x: 4, y: 4 }, 'ArrowRight', 5)).toEqual({ x: 4, y: 4 })
    expect(stepCursor({ x: 4, y: 4 }, 'ArrowDown', 5)).toEqual({ x: 4, y: 4 })
  })

  it('ignores any other key', () => {
    expect(stepCursor(middle, 'Enter', 5)).toBeNull()
    expect(stepCursor(middle, 'a', 5)).toBeNull()
  })
})

describe('capitalOf', () => {
  it('names the player whose capital sits on a tile', () => {
    expect(capitalOf(sample(), { x: 0, y: 0 })?.id).toBe('a')
    expect(capitalOf(sample(), { x: 1, y: 1 })?.id).toBe('b')
  })

  it('leaves an ordinary tile alone', () => {
    expect(capitalOf(sample(), { x: 1, y: 0 })).toBeUndefined()
  })

  it('still finds a capital the owner has lost', () => {
    const game = sample()
    game.players[0].capital_lost = 2
    expect(capitalOf(game, { x: 0, y: 0 })?.capital_lost).toBe(2)
  })
})
