import { BuildingKind, Coord, Game, TileKind } from '../types/schema'
import { BUILDING_COST } from '../lib/board'
import { PALETTE } from '../utils/palette'

interface InspectorProps {
  game: Game
  myId: string | null
  picked: Coord | null
  myTurn: boolean
  onBuild: (source: Coord, building: BuildingKind) => void
}

const LABELS: Record<BuildingKind, string> = {
  [BuildingKind.FARM]: 'farm',
  [BuildingKind.FORT]: 'fort'
}

export function Inspector({ game, myId, picked, myTurn, onBuild }: InspectorProps) {
  const tile = picked ? game.tiles[picked.y]?.[picked.x] : undefined
  const me = game.players.find((player) => player.id === myId)
  const owner = tile?.owner ? game.players.find((player) => player.id === tile.owner) : undefined
  const mine = Boolean(tile && tile.owner === myId)
  const buildable = mine && tile?.kind === TileKind.LAND

  return (
    <section className="section">
      <h2 className="label">tile</h2>

      {!tile || !picked ? (
        <p className="muted">pick a tile to look at it</p>
      ) : (
        <>
          <p className="turn-line">
            ({picked.x}, {picked.y})
          </p>
          <dl className="facts">
            <dt>ground</dt>
            <dd>{tile.kind}</dd>
            <dt>owner</dt>
            <dd>
              {owner ? (
                <>
                  <span className="chip" style={{ backgroundColor: PALETTE[owner.color].fill }} />
                  {owner.name}
                </>
              ) : (
                'nobody'
              )}
            </dd>
            <dt>soldiers</dt>
            <dd>{tile.soldiers}</dd>
            <dt>built</dt>
            <dd>{tile.buildings.length ? tile.buildings.map((kind) => LABELS[kind]).join(' + ') : 'nothing'}</dd>
          </dl>

          {buildable && (
            <div className="builds">
              {tile.buildings.length < 2 ? (
                (Object.keys(LABELS) as BuildingKind[]).map((kind) => (
                  <button
                    key={kind}
                    className="btn"
                    disabled={!myTurn || Boolean(me && me.gold < BUILDING_COST) || tile.buildings.includes(kind)}
                    onClick={() => onBuild(picked, kind)}
                  >
                    {tile.buildings.includes(kind)
                      ? `${LABELS[kind]} built`
                      : `build ${LABELS[kind]} · ${BUILDING_COST}`}
                  </button>
                ))
              ) : (
                <p className="muted">nothing more fits here</p>
              )}
            </div>
          )}
        </>
      )}
    </section>
  )
}
