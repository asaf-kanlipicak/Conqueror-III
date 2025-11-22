import { useState, useEffect, useRef } from 'react'
import { API_BASE_URL } from '../config'

export function useGameState() {
    const [grid, setGrid] = useState<number[][]>([])
    const ws = useRef<WebSocket | null>(null)

    useEffect(() => {
        ws.current = new WebSocket(API_BASE_URL)

        ws.current.onopen = () => {
            console.log('Connected to WebSocket')
        }

        ws.current.onerror = (error) => {
            console.error('WebSocket error:', error)
        }

        ws.current.onclose = () => {
            console.log('WebSocket connection closed')
        }

        ws.current.onmessage = (event) => {
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
            ws.current?.close()
        }
    }, [])

    const handleTileClick = (x: number, y: number) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ x, y }))
        }
    }

    return { grid, handleTileClick }
}
