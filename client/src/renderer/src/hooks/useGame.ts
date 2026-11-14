import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { API_BASE_URL } from '../config'
import { playChime, playClick, shouldChime, shouldClickChat } from '../lib/chime'
import {
  CommandType,
  Coord,
  ErrorData,
  Game,
  GameMessage,
  MessageType,
  PendingOrder,
  Player,
  PlayerColor
} from '../types/schema'

const STORAGE_KEY = 'conqueror.player'
const RETRY_MS = 1500
const NOTICE_MS = 5000

export interface GameSession {
  game: Game | null
  myId: string | null
  me: Player | null
  myTurn: boolean
  orders: PendingOrder[]
  error: string | null
  status: 'connecting' | 'live' | 'offline'
  join: (name: string, color: PlayerColor) => void
  start: (size: number) => void
  reset: () => void
  order: (source: Coord, target: Coord, repeat?: boolean) => void
  cancel: (source: Coord) => void
  chat: (text: string) => void
  endTurn: () => void
}

export function useGame(): GameSession {
  const [game, setGame] = useState<Game | null>(null)
  const [myId, setMyId] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY))
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<GameSession['status']>('connecting')
  const socket = useRef<WebSocket | null>(null)
  const resuming = useRef(false)

  useEffect(() => {
    let disposed = false
    let retry: number | undefined

    const connect = (): void => {
      const ws = new WebSocket(API_BASE_URL)
      socket.current = ws
      setStatus('connecting')

      ws.onopen = (): void => {
        setStatus('live')
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) {
          resuming.current = true
          ws.send(JSON.stringify({ type: CommandType.RESUME, data: { player_id: stored } }))
        }
      }

      ws.onmessage = (event): void => {
        const message = JSON.parse(event.data) as GameMessage
        switch (message.type) {
          case MessageType.CONNECT_SUCCESS:
            setGame(message.data as Game)
            break
          case MessageType.GAME_UPDATE: {
            const next = message.data as Game
            setGame(next)
            const stored = localStorage.getItem(STORAGE_KEY)
            const index = next.players.findIndex((player) => player.id === stored)
            if (index < 0 && (next.started || next.players.length === 0)) {
              localStorage.removeItem(STORAGE_KEY)
              setMyId(null)
            }
            break
          }
          case MessageType.JOIN_SUCCESS: {
            const player = message.data as Player
            resuming.current = false
            setMyId(player.id)
            localStorage.setItem(STORAGE_KEY, player.id)
            break
          }
          case MessageType.ERROR:
            setError((message.data as ErrorData).message)
            if (resuming.current) {
              resuming.current = false
              setMyId(null)
              localStorage.removeItem(STORAGE_KEY)
            }
            break
        }
      }

      ws.onclose = (): void => {
        if (disposed) return
        setStatus('offline')
        retry = window.setTimeout(connect, RETRY_MS)
      }

      ws.onerror = (): void => ws.close()
    }

    connect()

    return () => {
      disposed = true
      window.clearTimeout(retry)
      socket.current?.close()
      socket.current = null
    }
  }, [])

  useEffect(() => {
    if (!error) return
    const timer = window.setTimeout(() => setError(null), NOTICE_MS)
    return () => window.clearTimeout(timer)
  }, [error])

  const send = useCallback((type: CommandType, data?: unknown): void => {
    const ws = socket.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    ws.send(JSON.stringify(data === undefined ? { type } : { type, data }))
  }, [])

  const myIndex = game ? game.players.findIndex((player) => player.id === myId) : -1
  const me = game && myIndex >= 0 ? game.players[myIndex] : null
  const myTurn = Boolean(game?.started && !game?.winner && myIndex >= 0 && myIndex === game?.turn)
  const orders = useMemo(() => (game?.orders ?? []).filter((order) => order.player === myId), [game, myId])

  const wasMyTurn = useRef<boolean | null>(null)
  useEffect(() => {
    if (shouldChime(wasMyTurn.current, myTurn)) playChime()
    wasMyTurn.current = myTurn
  }, [myTurn])

  const lastChat = useRef(0)
  useEffect(() => {
    if (!game) return
    const line = game.chat[game.chat.length - 1]
    if (!line) return
    const seen = lastChat.current
    lastChat.current = line.at
    const fromMe = line.name === game.players.find((player) => player.id === myId)?.name
    if (shouldClickChat(seen, line.at, fromMe)) playClick()
  }, [game, myId])

  const join = useCallback((name: string, color: PlayerColor) => send(CommandType.JOIN, { name, color }), [send])
  const start = useCallback((size: number) => send(CommandType.START, { size }), [send])
  const reset = useCallback(() => send(CommandType.RESET), [send])
  const order = useCallback(
    (source: Coord, target: Coord, repeat?: boolean) =>
      send(CommandType.MOVE, repeat === undefined ? { source, target } : { source, target, repeat }),
    [send]
  )
  const cancel = useCallback((source: Coord) => send(CommandType.CANCEL, { source }), [send])
  const chat = useCallback((text: string) => send(CommandType.CHAT, { text }), [send])
  const endTurn = useCallback(() => send(CommandType.END_TURN), [send])

  return {
    game,
    myId,
    me,
    myTurn,
    orders,
    error,
    status,
    join,
    start,
    reset,
    order,
    cancel,
    chat,
    endTurn
  }
}
