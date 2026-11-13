import { useEffect, useState } from 'react'
import { Coord, Game, Move, Player } from '../types/schema'
import { OrderList } from './OrderList'

interface TurnPanelProps {
  game: Game
  myId: string | null
  myTurn: boolean
  orders: Move[]
  onCancelOrder: (source: Coord) => void
  onCancelAll: () => void
  onEndTurn: () => void
  onReset: () => void
}

export function TurnPanel({
  game,
  myId,
  myTurn,
  orders,
  onCancelOrder,
  onCancelAll,
  onEndTurn,
  onReset
}: TurnPanelProps) {
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    if (!confirming) return
    const timer = window.setTimeout(() => setConfirming(false), 3000)
    return () => window.clearTimeout(timer)
  }, [confirming])

  if (!game.started) return null

  const me: Player | null = game.players.find((player) => player.id === myId) ?? null
  const winner: Player | null = game.players.find((player) => player.id === game.winner) ?? null
  const active: Player | null = game.players[game.turn] ?? null

  return (
    <section className="section">
      <h2 className="label">orders</h2>

      {winner && <p className="stamp">{winner.name} wins</p>}

      {!winner && !me && <p className="turn-line">watching</p>}

      {!winner && me?.eliminated && (
        <>
          <p className="turn-line">you are out</p>
          <p className="muted">your last tile is gone.</p>
        </>
      )}

      {!winner && me && !me.eliminated && (
        <>
          <p className="turn-line">{myTurn ? 'your move' : `waiting for ${active?.name ?? '…'}`}</p>
          {myTurn && (
            <OrderList game={game} myId={myId} orders={orders} onCancel={onCancelOrder} onCancelAll={onCancelAll} />
          )}
          <button className="btn" disabled={!myTurn} onClick={onEndTurn}>
            {orders.length === 0 ? 'end turn' : `end turn · ${orders.length} ordered`}
          </button>
        </>
      )}

      <div className="reset">
        <button
          className={`link${confirming ? ' confirming' : ''}`}
          onClick={() => {
            if (confirming) {
              onReset()
              setConfirming(false)
              return
            }
            setConfirming(true)
          }}
        >
          {confirming ? 'sure? this clears the table' : 'reset the table'}
        </button>
      </div>
    </section>
  )
}
