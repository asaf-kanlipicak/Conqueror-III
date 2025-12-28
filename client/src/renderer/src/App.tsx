import React from 'react'
import { useGameState } from './hooks/useGameState'
import { GameGrid } from './components/GameGrid'
import { Login } from './components/Login'
import { PlayerList } from './components/PlayerList'

function App(): React.JSX.Element {
  const { game, currentPlayer, joinGame, handleTileClick } = useGameState()

  if (!game) {
    // Waiting for connection
    return <div style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      width: '100vw',
      backgroundColor: '#1e1e1e',
      color: '#e0e0e0',
      gap: '1rem'
    }}>
      <div style={{ fontSize: '1.2rem' }}>Connecting to server...</div>
    </div>
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-evenly',
      alignItems: 'center',
      width: '100vw',
      height: '100vh',
      backgroundColor: '#1e1e1e',
      color: '#e0e0e0',
      padding: '2rem',
      boxSizing: 'border-box'
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <GameGrid grid={game.grid} onTileClick={handleTileClick} />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', minWidth: '300px' }}>
        {game.players && <PlayerList players={game.players.players} currentPlayer={currentPlayer} />}
        {!currentPlayer && <Login onJoin={joinGame} />}
      </div>
    </div>
  )
}

export default App
