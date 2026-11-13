import { PlayerColor } from '../types/schema'

interface Swatch {
  fill: string
  ink: string
}

export const INK = '#26221c'
export const NEUTRAL_FILL = '#ded5c3'
export const WATER_FILL = '#c6d6d6'

export const PALETTE: Record<PlayerColor, Swatch> = {
  [PlayerColor.RED]: { fill: '#a63d2f', ink: '#f7f1e5' },
  [PlayerColor.GREEN]: { fill: '#4d6b3a', ink: '#f7f1e5' },
  [PlayerColor.BLUE]: { fill: '#2f4f74', ink: '#f7f1e5' },
  [PlayerColor.YELLOW]: { fill: '#c1902f', ink: '#26221c' },
  [PlayerColor.ORANGE]: { fill: '#b25f28', ink: '#f7f1e5' },
  [PlayerColor.TURQUOISE]: { fill: '#2c7a76', ink: '#f7f1e5' },
  [PlayerColor.PURPLE]: { fill: '#6a4a72', ink: '#f7f1e5' },
  [PlayerColor.WHITE]: { fill: '#f4eee1', ink: '#26221c' }
}
