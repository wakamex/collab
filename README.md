# Arena

Arena is a collaborative bot tournament platform inspired by the game-AI and
agent-routing projects in `/code`.

It ships with:
- A deterministic Connect Four engine
- A bot router/registry for plug-in strategies
- A round-robin tournament runner with ELO ratings
- Rich leaderboard summaries (including head-to-head stats)
- Markdown/JSON export for collaboration logs and replay metadata

## Quick Start

Run a tournament with built-in bots:

```bash
python -m arena.cli --bots dex clod random greedy minimax mcts --rounds 2 --games-per-pair 2 --seed 42
```

Run the reproducible benchmark preset:

```bash
python -m arena.cli --preset baseline-6
```

Write a markdown report:

```bash
python -m arena.cli --bots dex clod random greedy minimax mcts --rounds 2 --games-per-pair 2 --seed 42 --markdown-out reports/leaderboard.md --json-out reports/matches.json
```

List available bots:

```bash
python -m arena.cli --list-bots
```

List available presets:

```bash
python -m arena.cli --list-presets
```

## Baseline Results

```
$ make bench
python -m arena.cli --preset baseline-6
Rank  Bot       Rating  G   W   L   D
----  --------  ------  --  --  --  --
   1  minimax   1406.4  30  27   1   2
   2  mcts      1292.9  30  21   9   0
   3  greedy    1232.4  30  17  12   1
   4  dex       1217.4  30  16  11   3
   5  random    1048.9  30   4  26   0
   6  clod      1001.9  30   2  28   0
```

## Built-in Bots

- `random`: random legal move
- `greedy`: immediate win/block + center preference
- `minimax`: alpha-beta minimax with heuristic evaluation
- `mcts`: Monte Carlo Tree Search with UCB1
- `hybrid`: **Advanced AI** - threat analysis + smart MCTS + positional evaluation
- `dex`: greedy profile (collaborator identity bot)
- `clod`: random profile (collaborator identity bot)

### Advanced AI Strategy

The `hybrid` bot implements a multi-phase strategy:
1. **Threat Detection**: Find immediate wins and forced blocks
2. **Threat Analysis**: Odd/even threat parity and winning positions
3. **Smart MCTS**: 2000 heuristic-guided simulations
4. **Positional Evaluation**: Center control and pattern recognition

See [AI_STRATEGY.md](AI_STRATEGY.md) for detailed technical documentation.

Try the hybrid bot:
```bash
python -m arena.cli --bots hybrid minimax mcts --rounds 2 --games-per-pair 2 --seed 42
```

## Collaborative Workflow

Add new strategies without changing engine internals:

1. Create a bot class that implements `choose_move(game, player, rng)`.
2. Register it in `arena/router.py` (or in your own script via `BotRouter`).
3. Run tournaments and compare ELO deltas in markdown reports.

## Benchmark Snapshot Workflow

Use the fixed benchmark preset and write markdown snapshots under `snapshots/`:

```bash
python -m arena.cli --preset baseline-6 --markdown-out snapshots/baseline-6-seed42.md
```

`reports/` is ignored (ephemeral), while `snapshots/` is intended for committed
baseline history.

## Test

```bash
pytest -q
```
