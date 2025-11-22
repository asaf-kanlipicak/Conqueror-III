import React from 'react'

interface GameGridProps {
    grid: number[][]
    onTileClick: (x: number, y: number) => void
}

export function GameGrid({ grid, onTileClick }: GameGridProps): React.JSX.Element {
    if (grid.length === 0) {
        return <div>Loading...</div>
    }

    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(20, 30px)',
            gap: '2px',
            backgroundColor: '#ccc',
            padding: '2px'
        }}>
            {grid.map((row, y) => (
                row.map((cell, x) => (
                    <div
                        key={`${x}-${y}`}
                        onClick={() => onTileClick(x, y)}
                        style={{
                            width: '30px',
                            height: '30px',
                            backgroundColor: cell === 1 ? 'black' : 'white',
                            cursor: 'pointer'
                        }}
                    />
                ))
            ))}
        </div>
    )
}
