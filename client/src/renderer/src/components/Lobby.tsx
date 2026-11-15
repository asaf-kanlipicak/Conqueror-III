import { useState } from 'react'
import { Game, PlayerColor } from '../types/schema'
import { BOARD_SIZES, SEATS } from '../lib/board'
import { PALETTE } from '../utils/palette'

interface LobbyProps {
  game: Game
  myId: string | null
  onJoin: (name: string, color: PlayerColor) => void
  onStart: (size: number) => void
  onShape: (size: number) => void
  onBot: () => void
}

export function Lobby({ game, myId, onJoin, onStart, onShape, onBot }: LobbyProps) {
  const [name, setName] = useState('')
  const [color, setColor] = useState<PlayerColor | null>(null)

  const seated = game.players.some((player) => player.id === myId)
  const taken = new Set(game.players.map((player) => player.color))

  if (game.started) {
    if (seated) return null
    return (
      <section className="section">
        <h2 className="label">the table</h2>
        <p className="muted">this game is under way. wait for the next one.</p>
      </section>
    )
  }

  return (
    <>
      {!seated && (
        <section className="section">
          <h2 className="label">take a seat</h2>
          <form
            onSubmit={(event) => {
              event.preventDefault()
              if (name.trim() && color) onJoin(name.trim(), color)
            }}
          >
            <div className="field">
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="your name"
                maxLength={20}
                required
              />
            </div>
            <div className="swatches">
              {Object.values(PlayerColor).map((candidate) => {
                const classes = ['swatch', color === candidate ? 'picked' : '', taken.has(candidate) ? 'taken' : '']
                return (
                  <button
                    key={candidate}
                    type="button"
                    className={classes.filter(Boolean).join(' ')}
                    style={{ backgroundColor: PALETTE[candidate].fill }}
                    disabled={taken.has(candidate)}
                    title={candidate}
                    onClick={() => setColor(candidate)}
                  />
                )
              })}
            </div>
            <button className="btn seat" type="submit" disabled={!name.trim() || !color}>
              join the table
            </button>
          </form>
        </section>
      )}

      <section className="section">
        <h2 className="label">the table</h2>
        <p className="muted">
          {game.players.length < 2 ? 'one more player is needed' : `${game.players.length} of ${SEATS} seats taken`}
        </p>
        <div className="sizes">
          {BOARD_SIZES.map((candidate) => (
            <button
              key={candidate}
              type="button"
              className={`size${game.size === candidate ? ' picked' : ''}`}
              onClick={() => onShape(candidate)}
            >
              {candidate} × {candidate}
            </button>
          ))}
        </div>
        <button className="link roll" onClick={() => onShape(game.size)}>
          roll a new map
        </button>
        {game.players.length < SEATS && (
          <button className="link roll" onClick={onBot}>
            add a bot
          </button>
        )}
        <button className="btn" disabled={game.players.length < 2} onClick={() => onStart(game.size)}>
          start the game
        </button>
      </section>
    </>
  )
}
