import { useEffect, useState } from 'react'
import { Coord, Game, PendingOrder, Player } from '../types/schema'
import { OrderList } from './OrderList'

interface TurnPanelProps {
  game: Game
  myId: string | null
  myTurn: boolean
  orders: PendingOrder[]
  onOrder: (source: Coord, target: Coord, repeat: boolean) => void
  onCancelOrder: (source: Coord, target?: Coord) => void
  onEndTurn: () => void
  onPause: (paused: boolean) => void
  onReset: () => void
}

export function TurnPanel({
  game,
  myId,
  myTurn,
  orders,
  onOrder,
  onCancelOrder,
  onEndTurn,
  onPause,
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
      {!winner && game.paused && <p className="stamp">paused</p>}

      {!winner && !me && <p className="turn-line">watching</p>}

      {!winner && me?.eliminated && (
        <>
          <p className="turn-line">you are out</p>
          <p className="muted">your last tile is gone.</p>
        </>
      )}

      {!winner && me && !me.eliminated && (
        <>
          <p className="turn-line">
            {game.paused ? 'on hold' : myTurn ? 'your move' : `waiting for ${active?.name ?? '…'}`}
          </p>
          <OrderList game={game} myId={myId} orders={orders} onOrder={onOrder} onCancel={onCancelOrder} />
          <button className="btn" disabled={!myTurn || game.paused} onClick={onEndTurn}>
            {game.paused
              ? 'the game is paused'
              : !myTurn
                ? 'waiting for your turn'
                : orders.length === 0
                  ? 'end turn'
                  : `end turn · ${orders.length} ordered`}
          </button>
        </>
      )}

      {game.started && (
        <div className="controls">
          {!winner && (
            <button className="link" onClick={() => onPause(!game.paused)}>
              {game.paused ? 'resume the game' : 'pause the game'}
            </button>
          )}
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
      )}
    </section>
  )
}
