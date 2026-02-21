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

Write a markdown report:

```bash
python -m arena.cli --bots dex clod random greedy minimax mcts --rounds 2 --games-per-pair 2 --seed 42 --markdown-out reports/leaderboard.md --json-out reports/matches.json
```

List available bots:

```bash
python -m arena.cli --list-bots
```

## Built-in Bots

- `random`: random legal move
- `greedy`: immediate win/block + center preference
- `minimax`: alpha-beta minimax with heuristic evaluation
- `mcts`: Monte Carlo Tree Search with UCB1
- `dex`: greedy profile (collaborator identity bot)
- `clod`: random profile (collaborator identity bot)

## Collaborative Workflow

Add new strategies without changing engine internals:

1. Create a bot class that implements `choose_move(game, player, rng)`.
2. Register it in `arena/router.py` (or in your own script via `BotRouter`).
3. Run tournaments and compare ELO deltas in markdown reports.

## Test

```bash
pytest -q
```
