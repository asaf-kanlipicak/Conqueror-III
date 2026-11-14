import { Board } from './components/Board'
import { Chat } from './components/Chat'
import { Lobby } from './components/Lobby'
import { LogFeed } from './components/LogFeed'
import { Roster } from './components/Roster'
import { TurnPanel } from './components/TurnPanel'
import { useGame } from './hooks/useGame'

function App() {
  const { game, myId, me, myTurn, orders, error, status, join, start, reset, order, cancel, cancelAll, chat, endTurn } =
    useGame()

  if (!game) {
    return (
      <main className="boot">
        <p className="label">{status === 'offline' ? 'looking for a table' : 'setting up'}</p>
      </main>
    )
  }

  return (
    <main className="app">
      <section className="stage">
        <div className="sheet">
          <header className="masthead">
            <h1>Conqueror III</h1>
            <span className="label">{game.started ? `round ${game.round}` : 'lobby'}</span>
          </header>

          <Board game={game} myId={myId} orders={orders} onOrder={order} onCancel={cancel} />

          {error && <p className="notice">{error}</p>}
          {status !== 'live' && <p className="notice">connection lost, coming back…</p>}
        </div>
      </section>

      <aside className="side">
        <Roster game={game} myId={myId} />
        <Lobby game={game} myId={myId} onJoin={join} onStart={start} />
        <TurnPanel
          game={game}
          myId={myId}
          myTurn={myTurn}
          orders={orders}
          onCancelOrder={cancel}
          onCancelAll={cancelAll}
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
