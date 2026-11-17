import { Game } from '../types/schema'
import { CAPITAL_GRACE, playerTotals } from '../lib/board'
import { PALETTE } from '../utils/palette'

interface RosterProps {
  game: Game
  myId: string | null
  onKick: (seat: string) => void
}

function countdown(lost: number): string {
  const left = CAPITAL_GRACE - lost
  return left === 1 ? 'capital: 1 round left' : `capital: ${left} rounds left`
}

export function Roster({ game, myId, onKick }: RosterProps) {
  return (
    <section className="section">
      <h2 className="label">seats</h2>
      {game.players.length === 0 && <p className="muted">nobody has taken a seat yet</p>}
      {game.players.length > 0 && (
        <div className="roster-head">
          <span />
          <span>name</span>
          <span>land</span>
          <span>soldiers</span>
          <span>gold</span>
          <span />
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
                <span className="name">
                  <span className="text">{player.name}</span>
                  {player.id === myId && <span className="tag">you</span>}
                  {player.bot && <span className="tag">bot</span>}
                  <span className={`dot${player.online ? ' live' : ''}`} title={player.online ? 'online' : 'away'} />
                </span>
                {player.capital_lost > 0 && !player.eliminated && (
                  <span className="alarm">{countdown(player.capital_lost)}</span>
                )}
              </span>
              <span className="figure">{totals.tiles}</span>
              <span className="figure">{totals.soldiers}</span>
              <span className="figure">{player.gold}</span>
              {game.started ? (
                <span />
              ) : (
                <button className="drop" title={`clear ${player.name}'s seat`} onClick={() => onKick(player.id)}>
                  ×
                </button>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
