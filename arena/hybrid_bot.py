from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

from .game import ConnectFour, EMPTY


@dataclass
class HybridBot:
    """
    Hybrid Connect Four AI combining threat-based solving with smart MCTS.
    
    Strategy:
    - Phase 1: Look for immediate wins and forced blocks
    - Phase 2: Use threat-based solver (odd/even threat analysis)
    - Phase 3: Smart MCTS with heuristics and pattern recognition
    - Phase 4: Positional evaluation fallback
    """

    name: str = "hybrid"
    simulations: int = 2000
    max_depth: int = 8
    
    def choose_move(self, game: ConnectFour, player: int, rng: random.Random) -> int:
        legal = game.legal_moves()
        if not legal:
            raise ValueError("No legal moves available")
        if len(legal) == 1:
            return legal[0]

        # Phase 1: Immediate wins and forced blocks
        win_move = self._find_immediate_win(game, player)
        if win_move is not None:
            return win_move

        block_move = self._find_immediate_win(game, -player)
        if block_move is not None:
            return block_move

        # Phase 2: Threat analysis
        threats = self._analyze_threats(game, player)
        if threats.winning_threats:
            return rng.choice(threats.winning_threats)
        if threats.blocks:
            critical_blocks = [b for b in threats.blocks if b in threats.opponent_threats]
            if critical_blocks:
                return rng.choice(critical_blocks)

        # Phase 3: Smart MCTS with heuristic guidance
        return self._smart_mcts(game, player, rng, legal)

    def _find_immediate_win(self, game: ConnectFour, player: int) -> Optional[int]:
        """Check if a player can win immediately."""
        for col in game.legal_moves():
            sim = game.clone()
            sim.current_player = player
            sim.drop(col)
            if sim.winner == player:
                return col
        return None

    def _analyze_threats(self, game: ConnectFour, player: int) -> ThreatAnalysis:
        """Analyze threats and winning positions."""
        threats = ThreatAnalysis()
        
        for col in game.legal_moves():
            # Check if we create a threat by playing here
            sim = game.clone()
            sim.drop(col)
            
            # Find all threats we create
            our_threats = self._find_threat_positions(sim, player)
            for threat_pos in our_threats:
                threats.our_threats.add((threat_pos, col))
            
            # Find all threats opponent creates
            opp_threats = self._find_threat_positions(sim, -player)
            for threat_pos in opp_threats:
                threats.opponent_threats.add((threat_pos, col))
            
            # Check if any of our threats are winning (can be played on next turn)
            for threat_pos in our_threats:
                if self._is_winning_threat(sim, threat_pos, player):
                    threats.winning_threats.append(col)
                    break
                
        # Find blocks needed
        for col in game.legal_moves():
            sim = game.clone()
            sim.current_player = -player
            sim.drop(col)
            if sim.winner == -player:
                threats.blocks.append(col)
                
        return threats

    def _find_threat_positions(self, game: ConnectFour, player: int) -> List[Tuple[int, int]]:
        """Find all positions where a player can win on their next turn."""
        threats = []
        legal = game.legal_moves()
        
        for col in legal:
            # Check if dropping here creates a win
            row = self._get_drop_row(game, col)
            if row is None:
                continue
                
            # Temporarily place piece
            game.board[row][col] = player
            
            # Check if this position creates a winning threat
            if self._is_four_in_a_row_position(game, row, col, player):
                threats.append((row, col))
            
            # Reset
            game.board[row][col] = EMPTY
            
        return threats

    def _get_drop_row(self, game: ConnectFour, col: int) -> Optional[int]:
        """Get the row where a piece would land in this column."""
        for row in range(game.rows - 1, -1, -1):
            if game.board[row][col] == EMPTY:
                return row
        return None

    def _is_four_in_a_row_position(self, game: ConnectFour, row: int, col: int, player: int) -> bool:
        """Check if placing a piece at this position would complete four in a row."""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for d_row, d_col in directions:
            count = 1  # The piece we're placing
            
            # Count in positive direction
            r, c = row + d_row, col + d_col
            while 0 <= r < game.rows and 0 <= c < game.cols and game.board[r][c] == player:
                count += 1
                r += d_row
                c += d_col
            
            # Count in negative direction
            r, c = row - d_row, col - d_col
            while 0 <= r < game.rows and 0 <= c < game.cols and game.board[r][c] == player:
                count += 1
                r -= d_row
                c -= d_col
            
            if count >= 4:
                return True
                
        return False

    def _is_winning_threat(self, game: ConnectFour, threat_pos: Tuple[int, int], player: int) -> bool:
        """Check if a threat can be played on the next turn."""
        row, col = threat_pos
        # For a threat to be playable on the next turn, the space below it must be filled
        if row == game.rows - 1:
            return True  # Bottom row
        return game.board[row + 1][col] != EMPTY

    def _smart_mcts(self, game: ConnectFour, player: int, rng: random.Random, legal: List[int]) -> int:
        """Run MCTS with smart move ordering and heuristics."""
        root = _HybridNode(move=None, parent=None, untried_moves=legal[:])
        root_state = game.clone()
        
        # Prioritize center and well-rated moves
        move_scores = self._score_moves(game, legal, player)
        
        for _ in range(self.simulations):
            node = root
            state = root_state.clone()
            
            # Selection with UCB1
            while node.is_fully_expanded and node.children:
                node = node.best_child(self._heuristic_score(state, player))
                state.drop(node.move)
            
            # Expansion
            if node.untried_moves and state.winner is None:
                # Prioritize high-scoring moves
                sorted_moves = sorted(
                    node.untried_moves,
                    key=lambda m: move_scores.get(m, 0),
                    reverse=True
                )
                move = sorted_moves[0] if rng.random() < 0.7 else rng.choice(node.untried_moves)
                node.untried_moves.remove(move)
                state.drop(move)
                child = _HybridNode(
                    move=move,
                    parent=node,
                    untried_moves=state.legal_moves()
                )
                node.children.append(child)
                node = child
            
            # Simulation with heuristics
            sim_state = state.clone()
            depth = 0
            while sim_state.winner is None and depth < 50:
                moves = sim_state.legal_moves()
                if not moves:
                    break
                
                # Heuristic-guided random play
                if rng.random() < 0.3:
                    move = rng.choice(moves)
                else:
                    move_scores = self._score_moves(sim_state, moves, player if depth % 2 == 0 else -player)
                    weights = [max(0.1, move_scores.get(m, 0) + 1) for m in moves]
                    total = sum(weights)
                    if total == 0:
                        move = rng.choice(moves)
                    else:
                        probs = [w / total for w in weights]
                        move = rng.choices(moves, weights=probs, k=1)[0]
                
                sim_state.drop(move)
                depth += 1
            
            # Backpropagation with dynamic reward
            result = sim_state.winner
            reward = self._calculate_reward(result, player, depth)
            
            while node is not None:
                node.visits += 1
                node.wins += reward
                node = node.parent
        
        # Select best move based on visits and win rate
        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.move

    def _score_moves(self, game: ConnectFour, moves: List[int], player: int) -> Dict[int, float]:
        """Score moves based on heuristics."""
        scores = {}
        center = game.cols // 2
        
        for move in moves:
            score = 0.0
            
            # Center preference (stronger in earlier moves)
            center_dist = abs(move - center)
            score += (3 - center_dist) * 5
            
            # Check for potential wins
            sim = game.clone()
            sim.drop(move)
            if sim.winner == player:
                score += 1000
            
            # Check for threats created
            threats = self._find_threat_positions(sim, player)
            score += len(threats) * 15
            
            # Check for opponent threats blocked
            opp_threats_before = len(self._find_threat_positions(game, -player))
            opp_threats_after = len(self._find_threat_positions(sim, -player))
            score += (opp_threats_before - opp_threats_after) * 10
            
            scores[move] = score
            
        return scores

    def _heuristic_score(self, game: ConnectFour, player: int) -> float:
        """Quick positional evaluation."""
        score = 0.0
        board = game.board
        rows, cols, n = game.rows, game.cols, game.connect_n
        center = cols // 2
        
        # Center column value
        for r in range(rows):
            if board[r][center] == player:
                score += 6
            elif board[r][center] == -player:
                score -= 6
        
        # Evaluate windows
        for r in range(rows):
            for c in range(cols):
                # Horizontal
                if c + n <= cols:
                    score += self._score_window([board[r][c + i] for i in range(n)], player)
                # Vertical
                if r + n <= rows:
                    score += self._score_window([board[r + i][c] for i in range(n)], player)
                # Diagonals
                if r + n <= rows and c + n <= cols:
                    score += self._score_window([board[r + i][c + i] for i in range(n)], player)
                if r - n + 1 >= 0 and c + n <= cols:
                    score += self._score_window([board[r - i][c + i] for i in range(n)], player)
        
        return score

    def _score_window(self, window: List[int], player: int) -> float:
        """Score a window of 4 positions."""
        own = window.count(player)
        opp = window.count(-player)
        empty = window.count(EMPTY)
        
        if own > 0 and opp > 0:
            return 0.0
        
        # Strong preference for creating multiple threats
        if own == 3 and empty == 1:
            return 100.0  # Winning threat
        if own == 2 and empty == 2:
            return 10.0   # Potential threat
        if opp == 3 and empty == 1:
            return -80.0  # Must block
        if opp == 2 and empty == 2:
            return -5.0   # Opponent potential
        
        return 0.0

    def _calculate_reward(self, winner: Optional[int], player: int, depth: int) -> float:
        """Calculate reward with depth penalty for faster wins."""
        if winner is None or winner == 0:
            return 0.5  # Draw
        elif winner == player:
            # Reward faster wins more
            return 1.0 - (depth / 100) * 0.1
        else:
            return 0.0


class ThreatAnalysis:
    """Container for threat analysis results."""
    def __init__(self):
        self.winning_threats: List[int] = []
        self.blocks: List[int] = []
        self.our_threats: Set[Tuple[Tuple[int, int], int]] = set()
        self.opponent_threats: Set[Tuple[Tuple[int, int], int]] = set()


class _HybridNode:
    """Enhanced MCTS node with heuristic integration."""
    
    __slots__ = ("move", "parent", "children", "wins", "visits", "untried_moves")
    
    def __init__(self, move: int | None, parent: Optional['_HybridNode'], untried_moves: List[int]):
        self.move = move
        self.parent = parent
        self.children: List['_HybridNode'] = []
        self.wins = 0.0
        self.visits = 0
        self.untried_moves = untried_moves
    
    @property
    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0
    
    @property
    def win_rate(self) -> float:
        if self.visits == 0:
            return 0.0
        return self.wins / self.visits
    
    def best_child(self, heuristic_bonus: float = 0, c: float = 1.414) -> '_HybridNode':
        """Select child with UCB1 + heuristic bonus."""
        log_parent = math.log(self.visits)
        
        def score(child: '_HybridNode') -> float:
            if child.visits == 0:
                return float('inf')
            exploitation = child.wins / child.visits
            exploration = c * math.sqrt(log_parent / child.visits)
            # Add small heuristic bonus for better move ordering
            return exploitation + exploration + (heuristic_bonus / 1000)
        
        return max(self.children, key=score)
    
    def best_move_child(self) -> '_HybridNode':
        """Select most visited child (robust choice)."""
        return max(self.children, key=lambda c: c.visits)
