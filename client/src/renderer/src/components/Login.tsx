import React, { useState } from 'react'
import { PlayerColor } from '../types/schema'
import { getColorClass } from '../utils/colors'

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
        <div className="flex flex-col items-center bg-zinc-900 p-6 rounded-xl shadow-lg border border-zinc-700 text-zinc-200 w-full self-start box-border">
            <h2 className="mb-4 text-white text-xl w-full">Join Game</h2>
            <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4 w-full">
                <div>
                    <label className="block mb-1.5 font-medium text-zinc-400 text-sm">Name</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="w-full p-2 rounded border border-zinc-600 text-sm bg-zinc-800 text-white outline-none box-border focus:border-blue-500 transition-colors"
                        placeholder="Enter your name"
                        required
                    />
                </div>

                <div>
                    <label className="block mb-1.5 font-medium text-zinc-400 text-sm">Color</label>
                    <div className="grid grid-cols-4 gap-3 justify-items-center">
                        {Object.values(PlayerColor).map((c) => (
                            <button
                                key={c}
                                type="button"
                                onClick={() => setColor(c)}
                                className={`w-8 h-8 rounded-full cursor-pointer p-0 transition-all ${getColorClass(c)} ${color === c ? 'border-2 border-white shadow-[0_0_8px_rgba(255,255,255,0.3)]' : 'border-2 border-transparent'
                                    }`}
                                title={c}
                            />
                        ))}
                    </div>
                </div>

                <button
                    type="submit"
                    className="mt-2 p-2.5 bg-blue-500 text-white border-none rounded-md text-sm font-semibold cursor-pointer transition-colors hover:bg-blue-600"
                >
                    Join
                </button>
            </form>
        </div>
    )
}
