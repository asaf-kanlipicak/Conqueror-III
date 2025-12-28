import React from 'react'
import { Grid } from '../types/schema'
import { getColorClass } from '../utils/colors'

interface GameGridProps {
    grid: Grid
    onTileClick: (x: number, y: number) => void
}

export function GameGrid({ grid, onTileClick }: GameGridProps): React.JSX.Element {
    if (!grid || !grid.tiles || grid.tiles.length === 0) {
        return <div>Loading...</div>
    }


    return (
        <div className="flex flex-col gap-[2px] bg-zinc-400 p-[2px] border-2 border-zinc-700">
            {grid.tiles.map((row, y) => (
                <div key={y} className="flex gap-[2px]">
                    {row.map((tile, x) => (
                        <div
                            key={`${x}-${y}`}
                            onClick={() => onTileClick(x, y)}
                            className={`w-[50px] h-[50px] cursor-pointer transition-colors duration-200 border border-black/10 ${getColorClass(tile.color)}`}
                            title={`(${x},${y}) ${tile.type}`}
                        />
                    ))}
                </div>
            ))}
        </div>
    )
}
