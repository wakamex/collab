# AI Strategy for Arena

## Overview

This document outlines the AI strategy that produced the strongest bot in the arena: **NegamaxBot**, which achieves a rating of ~1425 ELO and dominates all other bots including the previous champion (MinimaxBot at ~1283 ELO).

## Key Insight

Connect Four is a solved game — Player 1 wins with perfect play starting in the center column. The practical challenge is building a bot that approaches perfect play within the constraints of a pure-Python search. The winning strategy combines **deeper search** with **smarter search** through three complementary techniques.

## The Three Pillars

### 1. Transposition Table (Position Caching)

The same board position can be reached through different move orders. Without caching, the bot re-evaluates these positions wastefully. The transposition table stores evaluated positions with their scores, search depths, and bound types (exact, lower, upper).

**Impact**: Eliminates redundant subtree searches, effectively doubling the useful search depth for the same computation.

**Implementation**: Board snapshots (tuples of tuples) serve as hash keys. Each entry stores `(score, depth, flag, best_move)` where the flag indicates whether the score is exact or a bound.

### 2. Iterative Deepening with Move Ordering

Instead of searching directly to depth 8, the bot searches progressively: depth 1, then 2, then 3, ... up to 8. Each shallower search provides move-ordering hints for the deeper search.

**Why this matters**: Alpha-beta pruning is exponentially more effective with good move ordering. With perfect ordering, alpha-beta searches O(b^(d/2)) nodes instead of O(b^d). The iterative deepening overhead is small (~10% extra work) but the pruning improvement is massive.

**Move ordering priority**:
1. Transposition table best move (from previous iteration)
2. Killer moves (moves that caused beta cutoffs at the same depth)
3. Center-first column ordering (static heuristic)

### 3. Pre-Search Tactical Detection

Before entering the tree search, the bot checks for:
- **Immediate wins**: A single move that completes four in a row
- **Immediate blocks**: The opponent would win next turn without intervention
- **Double threats**: A move that simultaneously creates two winning threats

The double-threat detection is the most impactful: creating two threats at once guarantees a win since the opponent can only block one.

## Evaluation Function

At leaf nodes (depth 0), positions are scored using:

| Feature | Weight | Rationale |
|---------|--------|-----------|
| Center column pieces | ±3 | Center control enables more winning lines |
| 3-in-a-row (open) | +50 / -40 | Asymmetric: our threats > their threats |
| 2-in-a-row (open) | +5 / -3 | Seed for future threats |
| Double threats (2+ ways to win) | +300 / -250 | Nearly unblockable |
| Single immediate threat | +30 / -20 | Forcing move advantage |

The evaluation directly probes the board for threats by temporarily placing pieces and checking for wins — more expensive but much more accurate than pattern matching alone.

## Results

### Full Tournament (6 unique bots, 3 rounds, seed 42)

```
Rank  Bot       Rating  Games  W   L   D
   1  negamax   1388.9  30     28  2   0
   2  minimax   1334.3  30     24  6   0
   3  greedy    1173.0  30     13  17  0
   4  hybrid    1165.0  30     13  17  0
   5  mcts      1162.4  30     12  18  0
   6  random     976.3  30      0  30  0
```

### Head-to-Head vs Previous Champion

Negamax beats minimax **7-3** over 10 games (5 rounds, seed 42). The advantage comes primarily from deeper search (8 vs 6 ply) enabled by the transposition table, and the pre-search double-threat detection.

## What Didn't Work

- **Negamax formulation**: A pure negamax (negate-and-recurse) formulation was harder to get right than the classic min/max split with a root_player parameter. The sign conventions are error-prone.
- **Expensive move ordering at every node**: Cloning the game to check for wins/blocks in move ordering was too slow at inner nodes. Cheap ordering (TT + killers + center) works better.
- **Odd/even threat analysis**: While theoretically important in Connect Four, the added complexity in the evaluation didn't improve practical play strength.
- **MCTS hybrids**: The HybridBot's approach of combining MCTS with heuristics underperforms a well-tuned deep search.

## Future Improvements

1. **Bitboard representation**: Encoding positions as 64-bit integers would make win detection and evaluation 10-100x faster, enabling deeper search.
2. **Opening book**: Pre-computed best moves for the first 6-8 plies would save search time in the critical opening phase.
3. **Null-move pruning**: Skip the opponent's move to get a quick lower bound, pruning obviously winning positions faster.
4. **Late move reductions**: Search less-promising moves at reduced depth to extend the effective search horizon.
5. **History heuristic integration**: Track which moves cause cutoffs globally, not just per-depth killers.
