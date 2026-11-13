import { Coord, Game, Move } from '../types/schema'
import { isAttack } from '../lib/board'

interface OrderListProps {
  game: Game
  myId: string | null
  orders: Move[]
  onCancel: (source: Coord) => void
  onCancelAll: () => void
}

export function OrderList({ game, myId, orders, onCancel, onCancelAll }: OrderListProps) {
  if (orders.length === 0) return <p className="muted">no orders yet · pick one of your tiles</p>

  return (
    <>
      <ul className="order-list">
        {orders.map((move) => {
          const source = game.tiles[move.source.y][move.source.x]
          return (
            <li key={`${move.source.x}:${move.source.y}`}>
              <span className="tally">{source.soldiers}</span>
              <span className="arrow">→</span>
              <span className="where">
                {move.target.x}, {move.target.y}
              </span>
              <span className="kind">{isAttack(game, move, myId) ? 'attack' : 'move'}</span>
              <button className="drop" onClick={() => onCancel(move.source)} title="cancel">
                ×
              </button>
            </li>
          )
        })}
      </ul>
      {orders.length > 1 && (
        <button className="link clear-all" onClick={onCancelAll}>
          clear all
        </button>
      )}
    </>
  )
}
