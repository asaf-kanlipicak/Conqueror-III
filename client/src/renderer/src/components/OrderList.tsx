import { Coord, Game, PendingOrder } from '../types/schema'
import { isAttack, orderCount } from '../lib/board'

interface OrderListProps {
  game: Game
  myId: string | null
  orders: PendingOrder[]
  onOrder: (source: Coord, target: Coord, repeat: boolean) => void
  onCancel: (source: Coord) => void
  onCancelAll: () => void
}

export function OrderList({ game, myId, orders, onOrder, onCancel, onCancelAll }: OrderListProps) {
  if (orders.length === 0) return <p className="muted">nothing planned · pick one of your tiles</p>

  return (
    <>
      <ul className="order-list">
        {orders.map((move) => (
          <li key={`${move.source.x}:${move.source.y}`}>
            <span className="where">
              <span className="from">
                ({move.source.x}, {move.source.y})
              </span>
              {' → '}
              {`(${move.target.x}, ${move.target.y})`}
            </span>
            <span className="tally">{orderCount(game, move)}</span>
            <span className="kind">{isAttack(game, move, myId) ? 'attack' : 'move'}</span>
            <button
              className={`hold${move.repeat ? ' on' : ''}`}
              onClick={() => onOrder(move.source, move.target, !move.repeat)}
              title={move.repeat ? 'repeats every round' : 'one shot'}
            >
              ↻
            </button>
            <button className="drop" onClick={() => onCancel(move.source)} title="cancel">
              ×
            </button>
          </li>
        ))}
      </ul>
      {orders.length > 1 && (
        <button className="link clear-all" onClick={onCancelAll}>
          clear all
        </button>
      )}
    </>
  )
}
