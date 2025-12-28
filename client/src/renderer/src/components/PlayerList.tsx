import React from 'react'
import { Player } from '../types/schema'
import { getColorClass } from '../utils/colors'

interface PlayerListProps {
    players: Player[]
    currentPlayer: Player | null
}

export function PlayerList({ players, currentPlayer }: PlayerListProps): React.JSX.Element {
    return (
        <div className="p-6 border border-zinc-700 rounded-xl w-full bg-zinc-900 self-start shadow-lg text-zinc-200 box-border">
            <h3 className="mt-0 mb-4 border-b border-zinc-700 pb-2 text-white text-lg">Players</h3>
            <ul className="list-none p-0 m-0">
                {players.map((player) => {
                    const isCurrent = currentPlayer?.name === player.name
                    return (
                        <li key={player.name} className={`flex items-center mb-2 p-2 rounded-md ${isCurrent ? 'bg-blue-500/20 font-semibold text-white' : 'font-normal text-zinc-200'}`}>
                            <span
                                className={`w-4 h-4 rounded-full mr-2.5 border-2 border-white shadow-[0_0_5px_rgba(0,0,0,0.5)] ${getColorClass(player.color)}`}
                            ></span>
                            <span className="flex-1 overflow-hidden text-ellipsis whitespace-nowrap">
                                {player.name} {isCurrent ? '(You)' : ''}
                            </span>
                        </li>
                    )
                })}
            </ul>
        </div>
    )
}
