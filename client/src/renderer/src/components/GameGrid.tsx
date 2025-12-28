import React from 'react'
import { Grid, TileType, BotColor } from '../types/schema'

interface GameGridProps {
    grid: Grid
    onTileClick: (x: number, y: number) => void
}

export function GameGrid({ grid, onTileClick }: GameGridProps): React.JSX.Element {
    if (!grid || !grid.tiles || grid.tiles.length === 0) {
        return <div>Loading...</div>
    }

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '2px',
            backgroundColor: '#ccc',
            padding: '2px',
            border: '2px solid #333'
        }}>
            {grid.tiles.map((row, y) => (
                <div key={y} style={{ display: 'flex', gap: '2px' }}>
                    {row.map((tile, x) => (
                        <div
                            key={`${x}-${y}`}
                            onClick={() => onTileClick(x, y)}
                            style={{
                                width: '50px',
                                height: '50px',
                                backgroundColor: tile.color,
                                cursor: 'pointer',
                                border: tile.type === TileType.BOT && tile.color === BotColor.GREY ? 'none' : '1px solid rgba(0,0,0,0.1)',
                                transition: 'background-color 0.2s'
                            }}
                            title={`(${x},${y}) ${tile.type}`}
                        />
                    ))}
                </div>
            ))}
        </div>
    )
}
