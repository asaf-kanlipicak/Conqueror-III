import { useState } from 'react'
import { Game, PlayerColor } from '../types/schema'
import { PALETTE } from '../utils/palette'

interface LobbyProps {
  game: Game
  myId: string | null
  onJoin: (name: string, color: PlayerColor) => void
  onStart: () => void
}

export function Lobby({ game, myId, onJoin, onStart }: LobbyProps) {
  const [name, setName] = useState('')
  const [color, setColor] = useState<PlayerColor | null>(null)

  const seated = game.players.some((player) => player.id === myId)
  const taken = new Set(game.players.map((player) => player.color))

  if (seated) {
    if (game.started) return null
    return (
      <section className="section">
        <h2 className="label">the table</h2>
        <p className="muted">
          {game.players.length < 2 ? 'one more player is needed' : 'everyone else can still join'}
        </p>
        <button className="btn" disabled={game.players.length < 2} onClick={onStart}>
          start the game
        </button>
      </section>
    )
  }

  if (game.started) {
    return (
      <section className="section">
        <h2 className="label">the table</h2>
        <p className="muted">this game is under way. wait for the next one.</p>
      </section>
    )
  }

  return (
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
  )
}
