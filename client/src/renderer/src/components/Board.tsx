import { useMemo, useState } from 'react'
import { Coord, Game, Move, Tile, TileKind } from '../types/schema'
import { INK, NEUTRAL_FILL, PALETTE, WATER_FILL } from '../utils/palette'
import { boardSpan, isAdjacent, isAttack, odds, orderArrow, sameCoord, TILE_SIZE } from '../lib/board'

interface BoardProps {
  game: Game
  myId: string | null
  orders: Move[]
  onOrder: (source: Coord, target: Coord) => void
  onCancel: (source: Coord) => void
}

export function Board({ game, myId, orders, onOrder, onCancel }: BoardProps) {
  const [selected, setSelected] = useState<Coord | null>(null)
  const [hovered, setHovered] = useState<Coord | null>(null)

  const swatches = useMemo(
    () => new Map(game.players.map((player) => [player.id, PALETTE[player.color]])),
    [game.players]
  )

  const side = game.tiles.length
  const span = boardSpan(side)
  const myIndex = game.players.findIndex((player) => player.id === myId)
  const myTurn = game.started && !game.winner && myIndex >= 0 && myIndex === game.turn

  const tileAt = (coord: Coord): Tile => game.tiles[coord.y][coord.x]

  const click = (coord: Coord): void => {
    if (!myTurn) return
    if (orders.some((move) => sameCoord(move.source, coord))) {
      onCancel(coord)
      setSelected(coord)
      return
    }
    if (selected && isAdjacent(selected, coord)) {
      onOrder(selected, coord)
      setSelected(null)
      return
    }
    setSelected(tileAt(coord).owner === myId ? coord : null)
  }

  const caption = ((): string => {
    if (!myTurn) {
      if (game.winner) return 'the war is over'
      const active = game.players[game.turn]
      return active ? `waiting for ${active.name}` : ''
    }
    if (!selected) return 'pick one of your tiles'
    const source = tileAt(selected)
    if (!hovered || !isAdjacent(selected, hovered)) return `${source.soldiers} men · pick a neighbour`
    const target = tileAt(hovered)
    if (target.owner === myId) return `${source.soldiers} men joining ${target.soldiers}`
    if (target.soldiers === 0) return `walk in with ${source.soldiers}`
    const chance = Math.round(odds(source.soldiers, target.soldiers) * 100)
    return `${source.soldiers} vs ${target.soldiers} · ${chance}% to win the exchange`
  })()

  return (
    <div className="board-frame">
      <div className="board-area">
        <div
          className={`board${myTurn ? ' playable' : ''}`}
          style={{ gridTemplateColumns: `repeat(${side}, ${TILE_SIZE}px)` }}
          onMouseLeave={() => setHovered(null)}
        >
          {game.tiles.map((row, y) =>
            row.map((tile, x) => {
              const coord = { x, y }
              const swatch = tile.owner ? swatches.get(tile.owner) : undefined
              const fill = swatch ? swatch.fill : tile.kind === TileKind.WATER ? WATER_FILL : NEUTRAL_FILL
              const queued = orders.some((move) => sameCoord(move.source, coord))
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
          <defs>
            <marker
              id="arrow-attack"
              viewBox="0 0 12 12"
              refX="10"
              refY="6"
              markerWidth="12"
              markerHeight="12"
              markerUnits="userSpaceOnUse"
              orient="auto"
            >
              <path d="M0.5,1 L11,6 L0.5,11 z" className="head-attack" />
            </marker>
            <marker
              id="arrow-move"
              viewBox="0 0 12 12"
              refX="10"
              refY="6"
              markerWidth="12"
              markerHeight="12"
              markerUnits="userSpaceOnUse"
              orient="auto"
            >
              <path d="M0.5,1 L11,6 L0.5,11 z" className="head-move" />
            </marker>
          </defs>
          {orders.map((move) => {
            const attack = isAttack(game, move, myId)
            const arrow = orderArrow(move.source, move.target)
            const head = attack ? 'url(#arrow-attack)' : 'url(#arrow-move)'
            return (
              <g key={`${move.source.x}:${move.source.y}`}>
                <line {...arrow} className="arrow-casing" />
                <line {...arrow} markerEnd={head} className={attack ? 'arrow-attack' : 'arrow-move'} />
              </g>
            )
          })}
        </svg>
      </div>
      <p className="caption">{caption}</p>
    </div>
  )
}
