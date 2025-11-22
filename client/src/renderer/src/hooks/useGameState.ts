import { useState, useEffect, useRef } from 'react'
import { API_BASE_URL } from '../config'

export function useGameState() {
    const [grid, setGrid] = useState<number[][]>([])
    const ws = useRef<WebSocket | null>(null)

    useEffect(() => {
        const socket = new WebSocket(API_BASE_URL)
        ws.current = socket

        socket.onopen = () => {
            console.log('Connected to WebSocket')
        }

        socket.onerror = (error) => {
            console.error('WebSocket error:', error)
        }

        socket.onclose = () => {
            console.log('WebSocket connection closed')
        }

        socket.onmessage = (event) => {
            const message = JSON.parse(event.data)
            if (message.type === 'init') {
                setGrid(message.data)
            } else if (message.type === 'update') {
                setGrid((prevGrid) => {
                    const newGrid = [...prevGrid]
                    newGrid[message.y] = [...newGrid[message.y]]
                    newGrid[message.y][message.x] = message.val
                    return newGrid
                })
            }
        }

        return () => {
            socket.close()
        }
    }, [])

    const handleTileClick = (x: number, y: number) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ x, y }))
        }
    }

    return { grid, handleTileClick }
}
