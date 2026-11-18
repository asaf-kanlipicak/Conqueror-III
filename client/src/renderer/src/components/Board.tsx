import { CSSProperties, KeyboardEvent, MouseEvent, useMemo, useRef, useState } from 'react'
import { BuildingKind, Coord, Game, PendingOrder, Tile, TileKind } from '../types/schema'
import { INK, NEUTRAL_FILL, PALETTE, WATER_FILL } from '../utils/palette'
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
  sameCoord,
  stepCursor,
  TILE_SIZE
} from '../lib/board'

interface BoardProps {
  game: Game
  myId: string | null
  onSplit: (source: Coord, targets: Coord[]) => void
  onPick: (coord: Coord) => void
}

interface Tip {
  x: number
  y: number
  text: string
}

export function Board({ game, myId, onSplit, onPick }: BoardProps) {
  const [picked, setPicked] = useState<Coord | null>(null)
  const [split, setSplit] = useState<Coord[]>([])
  const [hovered, setHovered] = useState<Coord | null>(null)
  const [tip, setTip] = useState<Tip | null>(null)
  const area = useRef<HTMLDivElement>(null)

  const swatches = useMemo(
    () => new Map(game.players.map((player) => [player.id, PALETTE[player.color]])),
    [game.players]
  )

  const side = game.tiles.length
  const span = boardSpan(side)
  const me = game.players.find((player) => player.id === myId)
  const canPlay = game.started && !game.winner && Boolean(me) && !me?.eliminated
  const orders = game.orders

  const tileAt = (coord: Coord): Tile => game.tiles[coord.y][coord.x]

  const mine = (coord: Coord): boolean => myId !== null && tileAt(coord).owner === myId

  const mineAt = (coord: Coord): PendingOrder[] =>
    orders.filter((order) => order.player === myId && sameCoord(order.source, coord))

  const clearPlan = (coord: Coord): boolean => {
    if (!clearsPlan(picked, coord, mine(coord), mineAt(coord).length)) return false
    setSplit([])
    onSplit(coord, [])
    return true
  }

  const pick = (coord: Coord): void => {
    onPick(coord)
    if (clearPlan(coord)) return
    setPicked(coord)
    setSplit(mine(coord) ? mineAt(coord).map((order) => order.target) : [])
  }

  const moveCursor = (key: string): void => {
    const next = stepCursor(picked ?? { x: 0, y: 0 }, key, side)
    if (!next) return
    setHovered(next)
    pick(next)
  }

  const keyDown = (event: KeyboardEvent): void => {
    if (event.key.startsWith('Arrow')) {
      event.preventDefault()
      moveCursor(event.key)
      return
    }
    if (event.key === 'Delete' || event.key === 'Backspace') {
      event.preventDefault()
      if (picked) clearPlan(picked)
      return
    }
    if (event.key === 'Escape') {
      setPicked(null)
      setSplit([])
    }
  }

  const rightClick = (event: MouseEvent, coord: Coord): void => {
    event.preventDefault()
    if (!canPlay || !picked || !mine(picked)) return
    if (!sameCoord(picked, coord) && !isAdjacent(picked, coord)) return
    const next = split.some((target) => sameCoord(target, coord))
      ? split.filter((target) => !sameCoord(target, coord))
      : [...split, coord]
    setSplit(next)
    onSplit(picked, next)
  }

  const caption = ((): { line: string; hint: string } => {
    const quiet = (line: string, hint = '') => ({ line, hint })
    if (!game.started) return quiet('the table is being set')
    if (game.winner) return quiet('the war is over')
    if (game.paused) return quiet('the game is paused')
    if (!me) return quiet('watching from the rail')
    if (me.eliminated) return quiet('you are out')
    if (!picked) return quiet('click any tile to read it', 'right-click a neighbour to order')
    const source = tileAt(picked)
    if (!mine(picked)) {
      return quiet(source.soldiers > 0 ? `${source.soldiers} soldiers · not yours` : 'empty · not yours')
    }
    const ordered = mineAt(picked).length
    const hint = ordered > 0 ? 'click again to clear' : ''
    if (split.length > 1) {
      const share = Math.floor(source.soldiers / split.length)
      return { line: `${source.soldiers} soldiers · ${split.length} ways · ${share} each`, hint }
    }
    if (!hovered || !isAdjacent(picked, hovered)) {
      const line = ordered > 0 ? `${source.soldiers} soldiers · ${ordered} ordered` : `${source.soldiers} soldiers`
      return { line, hint: hint || 'right-click a neighbour' }
    }
    const target = tileAt(hovered)
    if (target.owner === myId) return { line: `${source.soldiers} soldiers joining ${target.soldiers}`, hint }
    if (target.soldiers === 0) return { line: `walk in with ${source.soldiers}`, hint }
    const chance = Math.round(odds(source.soldiers, guardOf(target)) * 100)
    return { line: `${source.soldiers} vs ${target.soldiers} · ${chance}% to win the exchange`, hint }
  })()

  const orderTip = (order: PendingOrder): string => {
    const target = tileAt(order.target)
    const count = orderCount(game, order)
    const mark = order.repeat ? '● ' : ''
    if (target.owner === order.player) return `${mark}${count} join ${target.soldiers}`
    if (target.soldiers === 0) return `${mark}walk in with ${count}`
    const chance = Math.round(odds(count, guardOf(target)) * 100)
    return `${mark}${count} vs ${target.soldiers} · ${chance}%`
  }

  const showTip = (point: { clientX: number; clientY: number }, order: PendingOrder): void => {
    const rect = area.current?.getBoundingClientRect()
    if (!rect) return
    setTip({ x: point.clientX - rect.left, y: point.clientY - rect.top, text: orderTip(order) })
  }

  return (
    <div className="board-frame" style={{ '--span': `${span}px` } as CSSProperties}>
      <div className="board-area" ref={area}>
        <div
          className={`board${canPlay ? ' playable' : ''}`}
          style={{ gridTemplateColumns: `repeat(${side}, ${TILE_SIZE}px)` }}
          tabIndex={0}
          onKeyDown={keyDown}
          onMouseLeave={() => setHovered(null)}
        >
          {game.tiles.map((row, y) =>
            row.map((tile, x) => {
              const coord = { x, y }
              const swatch = tile.owner ? swatches.get(tile.owner) : undefined
              const fill = swatch ? swatch.fill : tile.kind === TileKind.WATER ? WATER_FILL : NEUTRAL_FILL
              const queued = orders.some((order) => sameCoord(order.source, coord))
              const capital = capitalOf(game, coord)
              const mark = capital ? PALETTE[capital.color] : null
              const held = Boolean(capital && tile.owner === capital.id)
              const digits = tile.soldiers > 0 ? String(tile.soldiers).length : 0
              const classes = [
                'tile',
                tile.kind === TileKind.WATER ? 'water' : '',
                !tile.owner && tile.kind === TileKind.LAND ? 'neutral' : '',
                digits > 3 ? 'd4' : digits > 2 ? 'd3' : '',
                tile.buildings.includes(BuildingKind.FORT) ? 'fort' : '',
                tile.buildings.includes(BuildingKind.FARM) ? 'farm' : '',
                picked && sameCoord(picked, coord) ? 'picked' : '',
                hovered && sameCoord(hovered, coord) && picked && mine(picked) && isAdjacent(picked, coord)
                  ? 'target'
                  : '',
                split.some((target) => sameCoord(target, coord)) ? 'splitting' : '',
                queued ? 'queued' : ''
              ]
              return (
                <div
                  key={`${x}:${y}`}
                  data-coord={`${x},${y}`}
                  className={classes.filter(Boolean).join(' ')}
                  style={{ backgroundColor: fill, color: swatch ? swatch.ink : INK, '--fill': fill } as CSSProperties}
                  onClick={() => pick(coord)}
                  onContextMenu={(event) => rightClick(event, coord)}
                  onMouseEnter={() => setHovered(coord)}
                >
                  {tile.soldiers > 0 && <span>{tile.soldiers}</span>}
                  {capital && mark && (
                    <i
                      className={`star${held ? '' : ' lost'}`}
                      style={{ backgroundColor: held ? mark.ink : mark.stroke }}
                    />
                  )}
                </div>
              )
            })
          )}
        </div>

        <svg
          className="orders"
          width={span}
          height={span}
          aria-hidden="true"
          onContextMenu={(event) => event.preventDefault()}
        >
          {orders.map((order) => {
            const mine = order.player === myId
            const attack = isAttack(game, order, order.player)
            const { head, ...shaft } = orderArrow(order.source, order.target)
            const rival = mine ? null : swatches.get(order.player)?.stroke
            return (
              <g key={`${order.source.x}:${order.source.y}:${order.target.x}:${order.target.y}`}>
                <line {...shaft} className="arrow-casing" />
                <line
                  {...shaft}
                  className={mine ? (attack ? 'arrow-attack' : 'arrow-move') : 'arrow-rival'}
                  style={rival ? { stroke: rival } : undefined}
                  strokeDasharray={rival ? '6 4' : undefined}
                />
                <path
                  d={head}
                  className={`arrow-head${attack ? ' attack' : ''}`}
                  style={rival ? { fill: rival } : undefined}
                />
                {order.repeat && (
                  <circle
                    cx={shaft.x1}
                    cy={shaft.y1}
                    r={3.2}
                    className={`arrow-pin${attack ? ' attack' : ''}`}
                    style={rival ? { fill: rival } : undefined}
                  />
                )}
                <line
                  {...shaft}
                  className="arrow-hit"
                  onMouseEnter={(event) => showTip(event, order)}
                  onMouseLeave={() => setTip(null)}
                />
              </g>
            )
          })}
        </svg>

        {tip && (
          <span className="tip" style={{ left: tip.x, top: tip.y }}>
            {tip.text}
          </span>
        )}
      </div>
      <p className="caption">
        <span className="state">{caption.line}</span>
        <span className="footer">
          <span className="hint">{caption.hint}</span>
          <span className="coord">{hovered ? `(${hovered.x}, ${hovered.y})` : ''}</span>
        </span>
      </p>
    </div>
  )
}
