import { describe, expect, it } from 'vitest'
import { shouldChime, shouldClickChat } from './chime'

describe('chime', () => {
  it('rings only when the turn arrives', () => {
    expect(shouldChime(false, true)).toBe(true)
  })

  it('stays quiet on mount, on your own turn and on leaving it', () => {
    expect(shouldChime(null, true)).toBe(false)
    expect(shouldChime(true, true)).toBe(false)
    expect(shouldChime(true, false)).toBe(false)
    expect(shouldChime(null, false)).toBe(false)
  })
})

describe('chat click', () => {
  it('clicks once for a fresh line from someone else', () => {
    expect(shouldClickChat(100, 100.5, false)).toBe(true)
  })

  it('stays quiet for your own line, an old line and the first load', () => {
    expect(shouldClickChat(100, 100.5, true)).toBe(false)
    expect(shouldClickChat(100.5, 100.5, false)).toBe(false)
    expect(shouldClickChat(0, 100.5, false)).toBe(false)
  })
})
