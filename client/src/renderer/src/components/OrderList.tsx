import { useState } from 'react'
import { Coord, Game, PendingOrder } from '../types/schema'
import { isAttack, orderCount, shownOrders } from '../lib/board'

interface OrderListProps {
  game: Game
  myId: string | null
  orders: PendingOrder[]
  onOrder: (source: Coord, target: Coord, repeat: boolean) => void
  onCancel: (source: Coord, target?: Coord) => void
}

export function OrderList({ game, myId, orders, onOrder, onCancel }: OrderListProps) {
  const [hideStanding, setHideStanding] = useState(false)

  const standing = orders.filter((order) => order.repeat)
  const shown = shownOrders(orders, hideStanding)

  return (
    <>
      {standing.length > 0 && (
        <div className="order-head">
          <span className="count">{orders.length} planned</span>
          <button className="link" onClick={() => setHideStanding(!hideStanding)}>
            {hideStanding ? `show ${standing.length} standing` : `hide ${standing.length} standing`}
          </button>
        </div>
      )}

      {shown.length === 0 && (
        <p className="muted">
          {orders.length === 0 ? 'nothing planned · pick one of your tiles' : 'only standing orders'}
        </p>
      )}

      {shown.length > 0 && (
        <ul className="order-list">
          {shown.map((move) => (
            <li key={`${move.source.x}:${move.source.y}:${move.target.x}:${move.target.y}`}>
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
                title={move.repeat ? 'standing · runs every round' : 'one shot'}
              >
                <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
                  <circle
                    cx="6"
                    cy="6"
                    r="4.4"
                    fill={move.repeat ? 'currentColor' : 'none'}
                    stroke="currentColor"
                    strokeWidth="1.4"
                  />
                </svg>
              </button>
              <button className="drop" onClick={() => onCancel(move.source, move.target)} title="cancel">
                ×
              </button>
            </li>
          ))}
        </ul>
      )}

      {shown.length > 1 && (
        <button className="link clear-all" onClick={() => shown.forEach((move) => onCancel(move.source, move.target))}>
          {hideStanding ? `clear these ${shown.length}` : 'clear all'}
        </button>
      )}
    </>
  )
}
