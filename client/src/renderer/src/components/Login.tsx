import React, { useState } from 'react'
import { PlayerColor } from '../types/schema'

interface LoginProps {
    onJoin: (name: string, color: PlayerColor) => void
}

export function Login({ onJoin }: LoginProps): React.JSX.Element {
    const [name, setName] = useState('')
    const [color, setColor] = useState<PlayerColor>(PlayerColor.BLUE)

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (name.trim()) {
            onJoin(name, color)
        }
    }

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            backgroundColor: '#1e1e1e',
            padding: '1.5rem',
            borderRadius: '12px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
            border: '1px solid #333',
            color: '#e0e0e0',
            width: '250px',
            alignSelf: 'flex-start'
        }}>
            <h2 style={{ marginBottom: '1rem', color: '#fff', fontSize: '1.25rem', width: '100%' }}>Join Game</h2>
            <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '1rem', width: '100%' }}>
                <div>
                    <label style={{ display: 'block', marginBottom: '0.4rem', fontWeight: 500, color: '#aaa', fontSize: '0.9rem' }}>Name</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '0.5rem',
                            borderRadius: '4px',
                            border: '1px solid #444',
                            fontSize: '0.9rem',
                            backgroundColor: '#2d2d2d',
                            color: '#fff',
                            outline: 'none',
                            boxSizing: 'border-box'
                        }}
                        placeholder="Enter your name"
                        required
                    />
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '0.4rem', fontWeight: 500, color: '#aaa', fontSize: '0.9rem' }}>Color</label>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                        {Object.values(PlayerColor).map((c) => (
                            <button
                                key={c}
                                type="button"
                                onClick={() => setColor(c)}
                                style={{
                                    width: '28px',
                                    height: '28px',
                                    backgroundColor: c,
                                    borderRadius: '50%',
                                    border: color === c ? '2px solid #fff' : '2px solid transparent',
                                    cursor: 'pointer',
                                    padding: 0,
                                    boxShadow: color === c ? '0 0 8px rgba(255,255,255,0.3)' : 'none',
                                    transition: 'all 0.2s'
                                }}
                                title={c}
                            />
                        ))}
                    </div>
                </div>

                <button
                    type="submit"
                    style={{
                        marginTop: '0.5rem',
                        padding: '0.6rem',
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '0.9rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'background-color 0.2s'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#3b82f6'}
                >
                    Join
                </button>
            </form>
        </div>
    )
}
