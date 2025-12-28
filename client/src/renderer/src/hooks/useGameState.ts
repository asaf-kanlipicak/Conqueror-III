import { useState, useEffect, useRef } from 'react'
import { API_BASE_URL } from '../config'
import {
    Game,
    Grid,
    Player,
    CommandType,
    EventType,
    ResultType,
    PlayerColor,
    JoinData,
    AttackData,
    TileUpdateData,
    Players
} from '../types/schema'

export function useGameState() {
    const [game, setGame] = useState<Game | null>(null)
    const [currentPlayer, setCurrentPlayer] = useState<Player | null>(null)
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
            console.log('WS Message:', message)

            // Handle Results (Responses to our commands or initial connection)
            if (message.type === ResultType.CONNECT_SUCCESS) {
                console.log('CONNECT_SUCCESS data:', message.data)
                setGame(message.data as Game)
            } else if (message.type === ResultType.JOIN_SUCCESS) {
                const player = message.data as Player
                setCurrentPlayer(player)
                console.log('Joined as', player)
            }

            // Handle Events (Broadcasts from server)
            else if (message.type === EventType.TILE_UPDATE) {
                const data = message.data as TileUpdateData
                setGame((prevGame) => {
                    if (!prevGame) return null
                    const newGridTiles = [...prevGame.grid.tiles]
                    newGridTiles[data.y] = [...newGridTiles[data.y]]
                    newGridTiles[data.y][data.x] = data.tile
                    return {
                        ...prevGame,
                        grid: {
                            ...prevGame.grid,
                            tiles: newGridTiles
                        }
                    }
                })
            } else if (message.type === EventType.PLAYERS_UPDATE) {
                const playersData = message.data as Players
                setGame((prevGame) => {
                    if (!prevGame) return null
                    return {
                        ...prevGame,
                        players: playersData
                    }
                })
            } else if (message.type === EventType.GRID_UPDATE) {
                const gridData = message.data as Grid
                setGame((prevGame) => {
                    if (!prevGame) return null
                    return {
                        ...prevGame,
                        grid: gridData
                    }
                })
            } else if (message.type === EventType.GAME_UPDATE) {
                const gameData = message.data as Game
                setGame(gameData)
                setCurrentPlayer(null)
            }
        }

        return () => {
            socket.close()
        }
    }, [])

    const joinGame = (name: string, color: PlayerColor) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            const joinData: JoinData = { name, color }
            ws.current.send(JSON.stringify({
                type: CommandType.JOIN,
                data: joinData
            }))
        }
    }

    const resetGame = () => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({
                type: CommandType.RESET
            }))
        }
    }

    const handleTileClick = (x: number, y: number) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN && currentPlayer) {
            const attackData: AttackData = { x, y }
            ws.current.send(JSON.stringify({
                type: CommandType.ATTACK,
                data: attackData
            }))
        }
    }

    return { game, currentPlayer, joinGame, handleTileClick, resetGame }
}
