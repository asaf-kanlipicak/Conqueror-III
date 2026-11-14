import { useEffect, useRef, useState } from 'react'
import { Game, Player } from '../types/schema'

interface ChatProps {
  game: Game
  me: Player | null
  onChat: (text: string) => void
}

export function Chat({ game, me, onChat }: ChatProps) {
  const [draft, setDraft] = useState('')
  const list = useRef<HTMLOListElement>(null)

  useEffect(() => {
    const element = list.current
    if (element) element.scrollTop = element.scrollHeight
  }, [game.chat.length])

  const send = (): void => {
    const text = draft.trim()
    if (!text) return
    onChat(text)
    setDraft('')
  }

  return (
    <section className="section chat-section">
      <h2 className="label">table talk</h2>
      {game.chat.length === 0 && <p className="muted">nothing said yet</p>}
      <ol className="chat" ref={list}>
        {game.chat.map((line, index) => (
          <li key={index}>
            <span className="speaker">{line.name}</span>
            <span>{line.text}</span>
          </li>
        ))}
      </ol>
      <form
        className="chat-form"
        onSubmit={(event) => {
          event.preventDefault()
          send()
        }}
      >
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={me ? 'say something' : 'join the table to talk'}
          disabled={!me}
          maxLength={200}
        />
        <button className="link" type="submit" disabled={!me || !draft.trim()}>
          send
        </button>
      </form>
    </section>
  )
}
