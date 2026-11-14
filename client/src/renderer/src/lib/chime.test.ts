import { describe, expect, it } from 'vitest'
import { shouldChime } from './chime'

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
