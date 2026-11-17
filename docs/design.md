# Conqueror III — Rules (v0.5)

A turn-based tile war game for 2–4 players. Every tile holds soldiers; you either move them into
your own land or send them against someone else's.

## Board

- 10×10 or 20×20, picked by whoever starts the game. Either way the map is split by a 2-tile-wide
  cross-shaped river into four quadrants.
- **Land** can be owned. **Water** can only be occupied: it starts empty, never holds a neutral
  garrison, and is never territory — a water tile emptied of soldiers is nobody's again.
- **Neutral land** ("bots") is scattered across the map: a garrison sitting on a pile of loot. The
  garrison grows the further a tile sits from the corner — cheapest next to your capital, strongest
  on the bank of the river — with a little noise so no two rings read the same.
- Each player starts with a capital in one corner, and nothing else.
- Moves and attacks are orthogonal only — no diagonals.

## Tiles

| kind         | owner    | soldiers           | production | loot                |
| ------------ | -------- | ------------------ | ---------- | ------------------- |
| player land  | player   | yes                | yes        | –                   |
| neutral land | none     | garrison           | –          | half the map's garrison |
| water        | none     | whoever moved in   | –          | none                |

A tile with 0 soldiers is empty: walking into it needs no roll and costs nothing.

## Players

- 2 to 4 players. Join order is turn order.
- Seats are taken in this order: top-left, bottom-right, top-right, bottom-left.
- Anyone can start the game once at least two have joined — seated or not, which is how a table of
  bots gets going.
- A seat can be cleared before the start, by anyone, including your own. The name and colour go back
  into the pool.
- A player with no land tiles left is out, and their soldiers still on water vanish. Soldiers on
  water never count as territory.
- A player whose connection drops keeps their tiles and soldiers. Queued orders that were never
  committed are dropped, their turn is skipped while they are away, and they can rejoin with their
  player id. Coming back earns a short grace period, so a reload does not cost a turn.
- **Pausing** stops the clock for everyone: no turn can be ended, the bots hold their plan, and a
  player who drops is marked away without losing their turn. Anyone at the table can pause or resume,
  which is how a game survives everyone closing the window. Resuming hands the turn on if whoever
  holds it is still away.

## Capitals

Each player starts on their seat, and that tile is their capital. It begins fortified, for free, and
carries a star in its owner's colour — the only mark on the board that is not about soldiers.

Losing it does not lose the game, but it starts a clock. At the end of every round the player does
not hold their capital, the clock ticks; three ticks and they are out. Taking it back resets the
clock to nothing. The fort does not come back with it: it was razed when the tile fell, and no
capital ever earns a second one.

A player who runs out of time is **not** wiped the way an ordinary loser is. Their land simply stops
being theirs: every tile they still hold turns neutral, keeps its garrison, keeps its forts, and
loses its farms — nobody farms for a flag that is gone. The garrison it happens to be holding becomes
the pile on the tile, half of it, so the territory stays on the board as a prize worth taking rather
than evaporating.

That is the second way to win, and the one that ends long games. Grinding a rival down to their last
tile takes a long time when both sides are dug in; standing on their capital for three rounds does
not.

## A turn

1. Queue orders. Each order picks one of your tiles and an orthogonally adjacent target:
   - target is yours → **transfer** all soldiers there
   - target is neutral, enemy, or occupied water → **attack** it with all soldiers
2. Orders can be queued at any time, including while someone else is playing. They wait for your
   turn, and everyone can see them. A plan dies with its tile: if you lose the source before your
   turn comes, the order is dropped.
3. A tile gives at most one order per target per turn. Several tiles may attack the same target.
4. **Splitting**: right-clicking neighbours instead of left-clicking them divides the tile's soldiers
   between every target picked, floor each, with the remainder left behind. The tile itself can be
   one of the picks, which is how you send half a stack and keep the other half at home. Four
   neighbours and 200 soldiers is 50 apiece; three ways is 66 each and 2 kept. A tile needs at least
   one soldier per way to split at all.
5. An order carries the soldiers the tile held when you gave it, so reinforcing a tile and ordering
   from it in the same turn sends only the original garrison onwards. The legs of a split carry their
   own share, so the second leg is unaffected by what the first one spent.
6. An order can be set to **stand**: it stays on its tile and runs again at the start of every one of
   your turns, carrying whatever the tile holds at that moment. That is how a supply line is kept
   running without re-issuing it. A standing order dies with its tile, like any other.
7. A **move** stands by default and an **attack** does not. Feeding your own land is the thing you
   want repeating — a tile's production keeps flowing down the line — while an attack is a one-off
   unless you deliberately make it a siege. Pointing an order at a different neighbour gives it that
   neighbour's default; leaving it alone keeps whatever you set.
8. End Turn: orders resolve one by one in the order you issued them, each rolling when it resolves.
   If a tile has become yours by the time a later order resolves, that order is just a transfer.
9. Production happens at the start of every round, for all players at once — including one round
   before the first turn. Turn order is join order.

Because a tile acts once per turn, a stack moves at most one tile per turn — standing orders
included: a line of them walks its soldiers forward one tile a round, not all at once.

## Battles

One roll decides the exchange. `a` = your soldiers on the source tile, `b` = soldiers on the target.
You win with probability `a / (a + b)`.

A **fort** makes the tile fight as if it held twice the soldiers: `b` becomes `2b` for the roll and
for the losses, but not for whether the tile falls. So an equal stack has a one-in-three chance, and
can take the tile outright if the roll lands.

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
- **Loot**: every neutral tile carries a pile fixed when the map is made — half the garrison it was
  built with — and whoever captures the tile takes it. Wearing a tile down over several attacks does
  not shrink the pile; the reward grows with the ring, so a soft tile pays a little and a river bank
  pays a lot.
- **Gold**: taking a bot tile also seizes a flat sum of gold. It is the only way to *earn* gold, so
  the early game is where the money is — once the neutral land is gone, nothing new is minted.
- **Interest**: whatever gold you are still holding pays 5% at the start of every round, capped at
  250. So a full treasury is not dead weight: sitting on it is a slow income, and spending it on a
  building is a bet that the building earns its keep sooner. It also means the gold column keeps
  moving in a long game, when there are no bots left to take it from.

## Buildings

Gold buys buildings, on your own land, on your own turn, 250 apiece.

| building | effect                                                        |
| -------- | ------------------------------------------------------------- |
| farm     | +25 soldiers on that tile every round, on top of production   |
| fort     | the tile defends as if it held twice the soldiers             |

- A tile can hold both, but gold is scarce enough that most tiles hold neither.
- Buildings are **razed** when the tile changes hands, and when an owner is wiped out. Taking a
  developed tile denies it to the enemy rather than inheriting it.
- No building on water.

## Feedback

- The server keeps a rolling log of the last 60 events — joins, battles, skipped turns,
  eliminations, the winner — and sends it with every update, so the UI can show a feed.
- Chat is a second capped list on the same update: who said what, last 50 lines, gone on reset.
  Anything not committed to an order is just talk. Someone else talking makes a short click.
- Your own turn is announced with a short chime. It rings on the change of turn only, so a reload
  does not set it off.
- Everyone's queued orders are drawn on the board: yours in ink, theirs in their colour. Hovering an
  arrow shows what it carries and the odds. A small pin at the tail marks an order that stands.
- A clock counts from the start of the game. A green dot marks a player who is at the table, a grey
  one who has stepped away.

## Winning

Last player with land tiles wins. A capital held for three rounds does the same job by another road:
it takes the loser's whole territory off the board, so the last one standing is decided by the same
rule either way.

Once it is over the table falls back to the lobby with everyone still seated, so the next game is one
click away — a fresh map, the same faces, the same bots.

## Bots

A bot takes a seat like anyone else and plays by the same rules. It has no hidden information and no
memory between turns: it plans from scratch, and the plan is public — the same arrows, visible while
the humans are playing.

The plan is a flow field. Every tile the bot does not own is a target; a breadth-first search over
land and water gives every tile its distance to the nearest one. Then, for each of the bot's tiles:

- adjacent to a target — it may strike. It sorts the neighbours by garrison and asks how many it can
  take at once: the largest `k` where an even share `a / k` still covers the k-th cheapest garrison.
  At `k` of one it works out its win chance against each neighbour, takes the best of them as its
  confidence, and rolls; a roll above that confidence means it holds and lets the field feed it,
  otherwise it picks a neighbour, weighted by those same chances, and attacks it. Above one it rolls
  against the share's own odds and, if the roll passes, splits the tile across the cheapest `k`
- otherwise — send everything one step down the field

Splitting is worth it because a share only has to match the garrison, not beat the whole stack: 300
soldiers against a 60 and a 90 can take both this turn with 150 apiece, where one attack would take
the 60 and leave the 90 standing. The test is per leg and not on the total, so 400 against 50, 50 and
350 still buys the two cheap ones even though the sum is larger than the stack.

So a tile at even odds attacks half the time, one at two to one about two thirds, and a tile facing
nothing better than a third attacks a third of the time. The same roll covers a hopeless case, so a
desperate push is possible but rare. It is not a decision about whether the attack is *wise*; it is
a decision about whether the bot feels lucky, which is what keeps two equal armies from standing
next to each other forever.

Because the flow only ever moves downhill, a stack walks one tile a turn and no two tiles swap. Open
water is part of the field, so a bot crosses the river the way it crosses land: one tile at a time,
with a stack that has to survive the crossing.

A bot that has lost its capital drops everything else. The field is rebuilt with the capital as its
only source, so every tile on the board flows at that one tile, and the whole army converges on the
retake. Nothing else is worth attacking with a three-round clock running.

A bot also has a **homeland**: the quarter its capital sits in, bounded by the river. Ground there
counts for more than ground anywhere else.

- Striking a homeland tile doubles the bot's willingness, so a coin flip at home reads as a certain
  attack. Nothing is capped — above even odds it simply always goes.
- The field charges one step to enter homeland ground and two to enter anywhere else. A target six
  steps away through its own quarter therefore costs what one three steps away costs across the
  river, which is how a bot is drawn home from further out than it would otherwise travel. The
  gradient stays strictly downhill, so the flow still cannot loop.

Gold follows one rule: **never spend down to nothing**, keep a margin above the price, spend the rest.

- A **fort** goes on a holding tile next to an enemy player, while the enemy could still be held at
  twice the garrison (`sum of adjacent enemy stacks ≤ 2 × garrison`), and only with 300 in hand.
  Holding tiles are the only ones the flow does not drain — anywhere else a fort would be left
  standing on an empty tile.
- A **farm** goes on the deepest tile the bot owns, and only once gold reaches 550. Spend at 250 and
  the bot would never have the coin for a fort when it finally needed one.

A bot's turn is announced, then played a second later, so the table sees the plan before it resolves.

## Starting constants (all tunable)

| constant                 | value        |
| ------------------------ | ------------ |
| board                    | 10×10, 20×20 |
| river width              | 2            |
| production per land tile | 10/turn      |
| loot per neutral tile    | half the garrison |
| gold per bot tile        | 100          |
| interest on held gold    | 5%/round, 250 cap |
| building cost            | 250          |
| farm bonus               | +25/turn     |
| fort defence             | ×2           |
| capital garrison         | 200          |
| capital grace            | 3 rounds     |
| homeland attack urge     | ×2           |
| neutral garrison         | 80–320, ±10% |
| players                  | 2–4          |

## Not in v1

Docks, ships, naval combat, tech trees, unit types, fog of war, extra win conditions.
