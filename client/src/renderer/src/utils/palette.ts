import { PlayerColor } from '../types/schema'

interface Swatch {
  fill: string
  ink: string
  stroke: string
}

export const INK = '#26221c'
export const NEUTRAL_FILL = '#ded5c3'
export const WATER_FILL = '#c6d6d6'

export const PALETTE: Record<PlayerColor, Swatch> = {
  [PlayerColor.RED]: { fill: '#a63d2f', ink: '#f7f1e5', stroke: '#8f2a1e' },
  [PlayerColor.GREEN]: { fill: '#4d6b3a', ink: '#f7f1e5', stroke: '#3b552b' },
  [PlayerColor.BLUE]: { fill: '#2f4f74', ink: '#f7f1e5', stroke: '#223f60' },
  [PlayerColor.YELLOW]: { fill: '#c1902f', ink: '#26221c', stroke: '#8a651c' },
  [PlayerColor.ORANGE]: { fill: '#b25f28', ink: '#f7f1e5', stroke: '#8c451a' },
  [PlayerColor.TURQUOISE]: { fill: '#2c7a76', ink: '#f7f1e5', stroke: '#1e5b58' },
  [PlayerColor.PURPLE]: { fill: '#6a4a72', ink: '#f7f1e5', stroke: '#523a58' },
  [PlayerColor.WHITE]: { fill: '#f4eee1', ink: '#26221c', stroke: '#8a8272' }
}
