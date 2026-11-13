# Conqueror III — Rules (v0.1)

A turn-based tile war game for 2–4 players. Every tile holds soldiers; you either move them into
your own land or send them against someone else's.

## Board

- 20×20 grid, split by a 2-tile-wide cross-shaped river into four quadrants.
- **Land** can be owned. **Water** can only be occupied: it starts empty, never holds a neutral
  garrison, and is never territory.
- **Neutral land** ("bots") is scattered across the map: a small garrison sitting on a pile of loot.
- Each player starts with a capital in one corner, and nothing else.
- Moves and attacks are orthogonal only — no diagonals.

## Tiles

| kind         | owner    | soldiers           | production | loot            |
| ------------ | -------- | ------------------ | ---------- | --------------- |
| player land  | player   | yes                | yes        | –               |
| neutral land | none     | garrison           | –          | yes, on capture |
| water        | none     | whoever moved in   | –          | none            |

A tile with 0 soldiers is empty: walking into it needs no roll and costs nothing.

## Players

- 2 to 4 players. Join order is turn order.
- Seats are taken in this order: top-left, bottom-right, top-right, bottom-left.
- Any player can start the game once at least two have joined.
- A player with no land tiles left is out, and their soldiers still on water vanish. Soldiers on
  water never count as territory.
- A player whose connection drops keeps their tiles and soldiers. Queued orders that were never
  committed are dropped, their turn is skipped while they are away, and they can rejoin with their
  player id. Coming back earns a short grace period, so a reload does not cost a turn.

## A turn

1. Queue orders. Each order picks one of your tiles and an orthogonally adjacent target:
   - target is yours → **transfer** all soldiers there
   - target is neutral, enemy, or occupied water → **attack** it with all soldiers
2. A tile gives at most one order per turn. Several tiles may attack the same target.
3. End Turn: orders resolve one by one in the order you issued them, each rolling when it resolves.
   If a tile has become yours by the time a later order resolves, that order is just a transfer.
4. Production happens at the start of every round, for all players at once — including one round
   before the first turn. Turn order is join order.

Because a tile acts once per turn, a stack moves at most one tile per turn.

## Battles

One roll decides the exchange. `a` = your soldiers on the source tile, `b` = soldiers on the target.
You win with probability `a / (a + b)`.

| outcome  | attacker loses     | defender loses     |
| -------- | ------------------ | ------------------ |
| you win  | `⌊a·b / (2(a+b))⌋` | `min(a, b)`        |
| you lose | `⌈a·b / (a+b)⌉`    | `⌊a·b / (2(a+b))⌋` |

- A won exchange kills at most `a` defenders, however large the garrison is.
- A tile changes hands only when its garrison reaches 0, and the winning stack advances onto it —
  attacking is a move you have to win. A repelled attack stays home.
- Winner's losses round down; a repelled attacker's losses round up.
- The winner always keeps at least one soldier.
- Empty targets are taken without a roll.
- Loot is paid only where there was a garrison to beat: walking into an undefended neutral tile
  gives nothing.

## Economy

- **Production**: every land tile you own produces a fixed number of soldiers at the start of each
  round, for all players simultaneously.
- **Loot**: neutral tiles carry a fixed amount, collected by whoever captures them. A neutral tile
  is worth ten turns of a single tile's production.

## Feedback

- The server keeps a rolling log of the last 60 events — joins, battles, skipped turns,
  eliminations, the winner — and sends it with every update, so the UI can show a feed.

## Winning

Last player with land tiles wins.

## Starting constants (all tunable)

| constant                 | value      |
| ------------------------ | ---------- |
| board                    | 20×20      |
| river width              | 2          |
| production per land tile | 10/turn    |
| loot per neutral tile    | 100        |
| capital garrison         | 200        |
| neutral garrison         | 0, 50–150  |
| players                  | 2–4        |

## Known issue (to fix)

- Chained transfers: give a row of your tiles one order each and resolution carries the same stack
  from tile to tile in a single turn, so the last tile attacks with the whole column. Fix direction:
  freeze each source's soldier count when the order is given, or forbid ordering from a tile that is
  also a target in the same turn.

## Not in v1

Docks, ships, naval combat, AI opponents, buildings, resources, fog of war, partial transfers,
extra win conditions.
