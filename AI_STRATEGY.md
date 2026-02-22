# AI Strategy for Arena Connect Four

## Overview

This branch introduces `HybridBot`, a state-of-the-art Connect Four AI that combines multiple strategic approaches to achieve strong performance while maintaining reasonable computational efficiency.

## Strategy Components

### 1. Threat-Based Solver (Phase 2)

The bot analyzes the board to detect "threats" - positions where a player can win on their next turn:

- **Immediate Wins**: If the bot can win immediately, it takes the win
- **Forced Blocks**: If the opponent can win immediately, the bot blocks
- **Threat Creation**: The bot identifies positions where playing creates a winning threat
- **Odd/Even Threat Analysis**: Connect Four is a "solved" game where threat parity matters - even threats (on even rows) and odd threats (on odd rows) have different strategic values

### 2. Smart MCTS (Phase 3)

Monte Carlo Tree Search enhanced with heuristics:

- **1200-2000 simulations** (configurable, default 2000)
- **UCB1 selection** with heuristic bonus for better move ordering
- **Heuristic-guided simulation**: 70% of playouts use weighted random selection based on position evaluation
- **Dynamic backpropagation**: Rewards faster wins more heavily

### 3. Positional Evaluation (Phase 4)

When MCTS doesn't find a clear winner, the bot evaluates positions using:

- **Center column preference**: Strong bonus for controlling the center (column 3)
- **Window scoring**: Evaluates all 4-cell windows across the board
  - Three own pieces + one empty = 100 points (winning threat)
  - Two own pieces + two empty = 10 points (potential threat)
  - Three opponent pieces + one empty = -80 points (must block)
  - Two opponent pieces + two empty = -5 points (opponent potential)

## Key Innovations

### Smart Move Ordering
Moves are scored before MCTS begins:
- Center distance penalty/bonus
- Immediate win detection
- Threat creation bonus
- Opponent threat blocking value

### Threat-Aware Simulation
During random playouts, moves are weighted by their heuristic value, making simulations more realistic than pure random play.

### Multi-Phase Decision
The bot uses a cascading decision process:
1. Win immediately if possible
2. Block opponent wins
3. Play winning threats (can win next turn)
4. Block critical opponent threats
5. Run smart MCTS with heuristic guidance

## Performance

The HybridBot achieves competitive performance:
- Beats greedy and random consistently
- Competes with minimax (depending on simulation count)
- Strong positional play throughout the game
- Better endgame performance than basic MCTS due to threat detection

## Configuration

```python
bot = HybridBot(
    name="hybrid",
    simulations=2000,  # Higher = stronger but slower
    max_depth=8        # For threat analysis
)
```

## Testing

10 comprehensive tests cover:
- Basic move generation
- Win detection and taking
- Block detection
- Threat analysis
- Center preference
- Reproducibility
- Integration with other bots

## Future Improvements

Potential enhancements for even stronger play:
1. **Transposition table**: Cache evaluated positions
2. **Opening book**: Pre-computed optimal early moves
3. **Endgame solver**: Perfect play when <10 moves remain
4. **Neural network evaluation**: Replace heuristic with trained value network
5. **Parallel MCTS**: Run simulations on multiple threads

## References

- [John Tromp's Connect Four solver](http://tromp.github.io/c4/c4.html)
- [AlphaZero paper](https://arxiv.org/abs/1712.01815)
- [MCTS survey](https://www.cs.put.poznan.pl/wjaskowski/pub/papers/2016-Browne-MCTS-Survey.pdf)
