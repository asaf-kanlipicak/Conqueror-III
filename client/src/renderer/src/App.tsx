import { useState } from 'react'
import { Board } from './components/Board'
import { Chat } from './components/Chat'
import { Elapsed } from './components/Elapsed'
import { Inspector } from './components/Inspector'
import { Lobby } from './components/Lobby'
import { LogFeed } from './components/LogFeed'
import { Roster } from './components/Roster'
import { TurnPanel } from './components/TurnPanel'
import { useGame } from './hooks/useGame'
import { Coord } from './types/schema'

function App() {
  const {
    game,
    myId,
    me,
    myTurn,
    orders,
    error,
    status,
    join,
    start,
    shape,
    reset,
    order,
    cancel,
    build,
    chat,
    endTurn
  } = useGame()
  const [picked, setPicked] = useState<Coord | null>(null)

  if (!game) {
    return (
      <main className="boot">
        <p className="label">{status === 'offline' ? 'looking for a table' : 'setting up'}</p>
      </main>
    )
  }

  return (
    <main className="app">
      <aside className="rail">
        <Inspector game={game} myId={myId} picked={picked} myTurn={myTurn} onBuild={build} />
      </aside>

      <section className="stage">
        <div className="sheet">
          <header className="masthead">
            <h1>Conqueror III</h1>
            <div className="stamp-line">
              {game.started_at !== null && <Elapsed startedAt={game.started_at} />}
              <span className="label">{game.started ? `round ${game.round}` : 'lobby'}</span>
            </div>
          </header>

          <Board
            key={`${game.started_at ?? 'lobby'}:${game.size}`}
            game={game}
            myId={myId}
            onOrder={order}
            onCancel={cancel}
            onPick={setPicked}
          />

          {error && <p className="notice">{error}</p>}
          {status !== 'live' && <p className="notice">connection lost, coming back…</p>}
        </div>
      </section>

      <aside className="side">
        <Roster game={game} myId={myId} />
        <Lobby game={game} myId={myId} onJoin={join} onStart={start} onShape={shape} />
        <TurnPanel
          game={game}
          myId={myId}
          myTurn={myTurn}
          orders={orders}
          onOrder={order}
          onCancelOrder={cancel}
          onEndTurn={endTurn}
          onReset={reset}
        />
        <Chat game={game} me={me} onChat={chat} />
        <LogFeed game={game} />
      </aside>
    </main>
  )
}

export default App
