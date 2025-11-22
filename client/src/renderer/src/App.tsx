import { useGameState } from './hooks/useGameState'
import { GameGrid } from './components/GameGrid'

function App(): React.JSX.Element {
  const { grid, handleTileClick } = useGameState()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px' }}>
      <h1>Tile Game</h1>
      <GameGrid grid={grid} onTileClick={handleTileClick} />
    </div>
  )
}

export default App
