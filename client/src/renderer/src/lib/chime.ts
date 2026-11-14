let context: AudioContext | null = null

const NOTES = [
  { frequency: 587.33, at: 0 },
  { frequency: 880, at: 0.12 }
]

export function shouldChime(wasMyTurn: boolean | null, isMyTurn: boolean): boolean {
  return wasMyTurn === false && isMyTurn
}

export function playChime(): void {
  context ??= new AudioContext()
  if (context.state === 'suspended') void context.resume()

  const now = context.currentTime
  for (const note of NOTES) {
    const oscillator = context.createOscillator()
    const gain = context.createGain()
    oscillator.type = 'sine'
    oscillator.frequency.value = note.frequency
    gain.gain.setValueAtTime(0, now + note.at)
    gain.gain.linearRampToValueAtTime(0.16, now + note.at + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.0001, now + note.at + 0.4)
    oscillator.connect(gain).connect(context.destination)
    oscillator.start(now + note.at)
    oscillator.stop(now + note.at + 0.42)
  }
}
