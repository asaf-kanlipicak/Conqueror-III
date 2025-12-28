import { PlayerColor, BotColor } from '../types/schema'

export const COLOR_MAP: Record<string, string> = {
    [PlayerColor.RED]: 'bg-red-500',
    [PlayerColor.GREEN]: 'bg-green-500',
    [PlayerColor.BLUE]: 'bg-blue-500',
    [PlayerColor.YELLOW]: 'bg-yellow-400',
    [PlayerColor.ORANGE]: 'bg-orange-500',
    [PlayerColor.TURQUOISE]: 'bg-cyan-400',
    [PlayerColor.PURPLE]: 'bg-purple-500',
    [PlayerColor.WHITE]: 'bg-white',
    [BotColor.GREY]: 'bg-zinc-500',
    [BotColor.BLACK]: 'bg-zinc-950'
}

export function getColorClass(color: string): string {
    return COLOR_MAP[color]
}
