let context: AudioContext | null = null

const NOTES = [
  { frequency: 587.33, at: 0 },
  { frequency: 880, at: 0.12 }
]

function audio(): AudioContext {
  context ??= new AudioContext()
  if (context.state === 'suspended') void context.resume()
  return context
}

export function shouldChime(wasMyTurn: boolean | null, isMyTurn: boolean): boolean {
  return wasMyTurn === false && isMyTurn
}

export function shouldClickChat(seenAt: number, at: number, fromMe: boolean): boolean {
  return seenAt !== 0 && at > seenAt && !fromMe
}

export function playChime(): void {
  const audioContext = audio()
  const now = audioContext.currentTime
  for (const note of NOTES) {
    const oscillator = audioContext.createOscillator()
    const gain = audioContext.createGain()
    oscillator.type = 'sine'
    oscillator.frequency.value = note.frequency
    gain.gain.setValueAtTime(0, now + note.at)
    gain.gain.linearRampToValueAtTime(0.16, now + note.at + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.0001, now + note.at + 0.4)
    oscillator.connect(gain).connect(audioContext.destination)
    oscillator.start(now + note.at)
    oscillator.stop(now + note.at + 0.42)
  }
}

export function playClick(): void {
  const audioContext = audio()
  const length = Math.floor(audioContext.sampleRate * 0.045)
  const buffer = audioContext.createBuffer(1, length, audioContext.sampleRate)
  const samples = buffer.getChannelData(0)
  for (let index = 0; index < length; index += 1) {
    samples[index] = (Math.random() * 2 - 1) * (1 - index / length) ** 6
  }

  const source = audioContext.createBufferSource()
  const filter = audioContext.createBiquadFilter()
  const gain = audioContext.createGain()
  source.buffer = buffer
  filter.type = 'bandpass'
  filter.frequency.value = 1900
  filter.Q.value = 1.1
  gain.gain.value = 0.16
  source.connect(filter).connect(gain).connect(audioContext.destination)
  source.start(audioContext.currentTime)
}
