import { Game } from '../types/schema'
import { playerTotals } from '../lib/board'
import { PALETTE } from '../utils/palette'

interface RosterProps {
  game: Game
  myId: string | null
}

export function Roster({ game, myId }: RosterProps) {
  return (
    <section className="section">
      <h2 className="label">seats</h2>
      {game.players.length === 0 && <p className="muted">nobody has taken a seat yet</p>}
      {game.players.length > 0 && (
        <div className="roster-head">
          <span />
          <span>name</span>
          <span>land</span>
          <span>men</span>
        </div>
      )}
      <ul className="roster">
        {game.players.map((player, index) => {
          const totals = playerTotals(game, player.id)
          const current = game.started && !game.winner && game.turn === index
          const classes = ['roster-row', player.eliminated ? 'out' : '', current ? 'current' : '']
          return (
            <li key={player.id} className={classes.filter(Boolean).join(' ')}>
              <span className="chip" style={{ backgroundColor: PALETTE[player.color].fill }} />
              <span className="who">
                {player.name}
                {player.id === myId && <span className="tag">you</span>}
                {!player.online && <span className="tag">away</span>}
              </span>
              <span className="figure">{totals.tiles}</span>
              <span className="figure">{totals.soldiers}</span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
