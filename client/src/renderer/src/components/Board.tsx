import { useMemo, useRef, useState } from 'react'
import { Coord, Game, PendingOrder, Tile, TileKind } from '../types/schema'
import { INK, NEUTRAL_FILL, PALETTE, WATER_FILL } from '../utils/palette'
import {
  boardSpan,
  clickTile,
  isAdjacent,
  isAttack,
  odds,
  orderArrow,
  orderCount,
  sameCoord,
  TILE_SIZE
} from '../lib/board'

interface BoardProps {
  game: Game
  myId: string | null
  onOrder: (source: Coord, target: Coord) => void
  onCancel: (source: Coord) => void
}

interface Tip {
  x: number
  y: number
  text: string
}

export function Board({ game, myId, onOrder, onCancel }: BoardProps) {
  const [selected, setSelected] = useState<Coord | null>(null)
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

  const mineAt = (coord: Coord): PendingOrder | undefined =>
    orders.find((order) => order.player === myId && sameCoord(order.source, coord))

  const click = (coord: Coord): void => {
    if (!canPlay) return
    const action = clickTile(selected, coord, tileAt(coord).owner === myId, Boolean(mineAt(coord)))
    if (action.kind === 'select') {
      setSelected(action.coord)
      return
    }
    if (action.kind === 'cancel') onCancel(action.source)
    else onOrder(action.source, action.target)
    setSelected(null)
  }

  const caption = ((): string => {
    if (!game.started) return 'the table is being set'
    if (game.winner) return 'the war is over'
    if (!me) return 'watching from the rail'
    if (me.eliminated) return 'you are out'
    if (!selected) return 'pick one of your tiles'
    const source = tileAt(selected)
    if (!hovered || !isAdjacent(selected, hovered)) return `${source.soldiers} soldiers · pick a neighbour`
    const target = tileAt(hovered)
    if (target.owner === myId) return `${source.soldiers} soldiers joining ${target.soldiers}`
    if (target.soldiers === 0) return `walk in with ${source.soldiers}`
    const chance = Math.round(odds(source.soldiers, target.soldiers) * 100)
    return `${source.soldiers} vs ${target.soldiers} · ${chance}% to win the exchange`
  })()

  const orderTip = (order: PendingOrder): string => {
    const target = tileAt(order.target)
    const count = orderCount(game, order)
    const mark = order.repeat ? '● ' : ''
    if (target.owner === order.player) return `${mark}${count} join ${target.soldiers}`
    if (target.soldiers === 0) return `${mark}walk in with ${count}`
    return `${mark}${count} vs ${target.soldiers} · ${Math.round(odds(count, target.soldiers) * 100)}%`
  }

  const showTip = (point: { clientX: number; clientY: number }, order: PendingOrder): void => {
    const rect = area.current?.getBoundingClientRect()
    if (!rect) return
    setTip({ x: point.clientX - rect.left, y: point.clientY - rect.top, text: orderTip(order) })
  }

  return (
    <div className="board-frame">
      <div className="board-area" ref={area}>
        <div
          className={`board${canPlay ? ' playable' : ''}`}
          style={{ gridTemplateColumns: `repeat(${side}, ${TILE_SIZE}px)` }}
          onMouseLeave={() => setHovered(null)}
        >
          {game.tiles.map((row, y) =>
            row.map((tile, x) => {
              const coord = { x, y }
              const swatch = tile.owner ? swatches.get(tile.owner) : undefined
              const fill = swatch ? swatch.fill : tile.kind === TileKind.WATER ? WATER_FILL : NEUTRAL_FILL
              const queued = orders.some((order) => sameCoord(order.source, coord))
              const digits = tile.soldiers > 0 ? String(tile.soldiers).length : 0
              const classes = [
                'tile',
                tile.kind === TileKind.WATER ? 'water' : '',
                !tile.owner && tile.kind === TileKind.LAND ? 'neutral' : '',
                digits > 3 ? 'd4' : digits > 2 ? 'd3' : '',
                selected && sameCoord(selected, coord) ? 'selected' : '',
                hovered && sameCoord(hovered, coord) && selected && isAdjacent(selected, coord) ? 'target' : '',
                queued ? 'queued' : ''
              ]
              return (
                <div
                  key={`${x}:${y}`}
                  data-coord={`${x},${y}`}
                  className={classes.filter(Boolean).join(' ')}
                  style={{ backgroundColor: fill, color: swatch ? swatch.ink : INK }}
                  onClick={() => click(coord)}
                  onMouseEnter={() => setHovered(coord)}
                >
                  {tile.soldiers > 0 && <span>{tile.soldiers}</span>}
                </div>
              )
            })
          )}
        </div>

        <svg className="orders" width={span} height={span} aria-hidden="true">
          {orders.map((order) => {
            const mine = order.player === myId
            const attack = isAttack(game, order, order.player)
            const { head, ...shaft } = orderArrow(order.source, order.target)
            const rival = mine ? null : swatches.get(order.player)?.stroke
            return (
              <g key={`${order.source.x}:${order.source.y}`}>
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
        <span>{caption}</span>
        {hovered && (
          <span className="coord">
            ({hovered.x}, {hovered.y})
          </span>
        )}
      </p>
    </div>
  )
}
