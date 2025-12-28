import React from 'react'
import { Player } from '../types/schema'

interface PlayerListProps {
    players: Player[]
    currentPlayer: Player | null
}

export function PlayerList({ players, currentPlayer }: PlayerListProps): React.JSX.Element {
    return (
        <div style={{
            padding: '1.5rem',
            border: '1px solid #333',
            borderRadius: '12px',
            width: '100%',
            backgroundColor: '#1e1e1e',
            alignSelf: 'flex-start',
            boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
            color: '#e0e0e0',
            boxSizing: 'border-box'
        }}>
            <h3 style={{ marginTop: 0, marginBottom: '1rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem', color: '#fff' }}>Players</h3>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {players.map((player) => {
                    const isCurrent = currentPlayer?.name === player.name
                    return (
                        <li key={player.name} style={{
                            display: 'flex',
                            alignItems: 'center',
                            marginBottom: '0.5rem',
                            padding: '0.5rem',
                            backgroundColor: isCurrent ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                            borderRadius: '6px',
                            fontWeight: isCurrent ? 600 : 400,
                            color: isCurrent ? '#fff' : '#e0e0e0'
                        }}>
                            <span style={{
                                width: '16px',
                                height: '16px',
                                backgroundColor: player.color,
                                borderRadius: '50%',
                                marginRight: '10px',
                                border: '2px solid #fff',
                                boxShadow: '0 0 5px rgba(0,0,0,0.5)'
                            }}></span>
                            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {player.name} {isCurrent ? '(You)' : ''}
                            </span>
                        </li>
                    )
                })}
            </ul>
        </div>
    )
}
