import { useEffect, useRef } from 'react'
import { Game } from '../types/schema'

interface LogFeedProps {
  game: Game
}

export function LogFeed({ game }: LogFeedProps) {
  const list = useRef<HTMLOListElement>(null)

  useEffect(() => {
    const element = list.current
    if (element) element.scrollTop = element.scrollHeight
  }, [game.log.length])

  return (
    <section className="section log-section">
      <h2 className="label">field notes</h2>
      {game.log.length === 0 && <p className="muted">nothing to report yet</p>}
      <ol className="log" ref={list}>
        {game.log.map((line, index) => (
          <li key={index}>{line}</li>
        ))}
      </ol>
    </section>
  )
}
