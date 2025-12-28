import React from 'react'
import { useGameState } from './hooks/useGameState'
import { GameGrid } from './components/GameGrid'
import { Login } from './components/Login'
import { PlayerList } from './components/PlayerList'

function App(): React.JSX.Element {
  const { game, currentPlayer, joinGame, handleTileClick, resetGame } = useGameState()

  if (!game) {
    // Waiting for connection
    return (
      <div className="flex flex-col justify-center items-center h-screen w-screen bg-zinc-900 text-zinc-200 gap-4">
        <div className="text-xl">Connecting to server...</div>
      </div>
    )
  }

  return (
    <div className="flex justify-evenly items-center w-screen h-screen bg-zinc-900 text-zinc-200 p-8 box-border">
      <div className="flex flex-col items-center">
        <GameGrid grid={game.grid} onTileClick={handleTileClick} />
      </div>

      <div className="flex flex-col gap-8 min-w-[250px]">
        {game.players && <PlayerList players={game.players.players} currentPlayer={currentPlayer} />}
        {!currentPlayer && <Login onJoin={joinGame} />}

        <button
          onClick={resetGame}
          className="p-2 bg-red-500 text-white border-none rounded-md text-sm font-semibold cursor-pointer mt-4 w-full hover:bg-red-600 transition-colors"
        >
          Reset Game
        </button>
      </div>
    </div>
  )
}

export default App
