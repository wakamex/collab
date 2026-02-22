import random
import pytest
from arena.hybrid_bot import HybridBot, ThreatAnalysis
from arena.game import ConnectFour


def test_bot_basic_interface():
    bot = HybridBot()
    game = ConnectFour()
    rng = random.Random(42)
    move = bot.choose_move(game, 1, rng)
    assert move in game.legal_moves()


def test_bot_prefers_winning_move():
    """Test that bot takes immediate wins."""
    bot = HybridBot(simulations=10)  # Low simulations for speed
    game = ConnectFour()
    rng = random.Random(42)
    
    # Set up board where player 1 can win in column 0
    # X X X . in bottom row
    for col in range(3):
        game.board[5][col] = 1
    
    move = bot.choose_move(game, 1, rng)
    assert move == 3  # Should complete four in a row


def test_bot_blocks_opponent_win():
    """Test that bot blocks opponent's winning moves."""
    bot = HybridBot(simulations=10)
    game = ConnectFour()
    rng = random.Random(42)
    
    # Set up board where opponent (-1) can win in column 0
    game.board[5][0] = -1
    game.board[5][1] = -1
    game.board[5][2] = -1
    
    move = bot.choose_move(game, 1, rng)
    assert move == 3  # Should block opponent


def test_bot_with_few_moves():
    """Test bot behavior when only one move is available."""
    bot = HybridBot(simulations=50)
    game = ConnectFour()
    rng = random.Random(42)
    
    # Fill almost all columns
    for col in range(6):
        for row in range(6):
            game.board[row][col] = 1 if (row + col) % 2 == 0 else -1
    
    # Only column 6 is legal
    legal = game.legal_moves()
    assert legal == [6]
    
    move = bot.choose_move(game, 1, rng)
    assert move == 6


def test_threat_analysis_empty_board():
    """Test threat analysis on empty board."""
    analysis = ThreatAnalysis()
    assert analysis.winning_threats == []
    assert analysis.blocks == []
    assert len(analysis.our_threats) == 0


def test_bot_center_preference_early_game():
    """Test that bot tends toward center in early game."""
    bot = HybridBot(simulations=100)
    game = ConnectFour()
    rng = random.Random(42)
    
    moves = []
    for _ in range(10):
        move = bot.choose_move(game, 1, rng)
        moves.append(move)
    
    # Center columns (2, 3, 4) should be preferred
    center_moves = sum(1 for m in moves if m in [2, 3, 4])
    assert center_moves >= 5  # At least half should be center-ish


def test_bot_reproducibility():
    """Test that bot produces reproducible results with same seed."""
    bot1 = HybridBot(simulations=50)
    bot2 = HybridBot(simulations=50)
    game1 = ConnectFour()
    game2 = ConnectFour()
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    
    # Play 5 moves with both bots
    for i in range(5):
        if game1.winner is not None or game2.winner is not None:
            break
        player = game1.current_player
        
        move1 = bot1.choose_move(game1, player, rng1)
        move2 = bot2.choose_move(game2, player, rng2)
        assert move1 == move2, f"Move {i}: {move1} != {move2}"
        
        game1.drop(move1)
        game2.drop(move2)


def test_score_moves_includes_all_legal():
    """Test that _score_moves returns scores for all legal moves."""
    bot = HybridBot()
    game = ConnectFour()
    legal = game.legal_moves()
    scores = bot._score_moves(game, legal, 1)
    
    assert len(scores) == len(legal)
    for move in legal:
        assert move in scores


def test_heuristic_score_symmetry():
    """Test that heuristic score is antisymmetric between players."""
    bot = HybridBot()
    game = ConnectFour()
    
    # Play a few moves
    game.drop(3)
    game.drop(2)
    game.drop(3)
    game.drop(4)
    
    score_p1 = bot._heuristic_score(game, 1)
    score_p2 = bot._heuristic_score(game, -1)
    
    # Scores should be roughly opposite (may not be exact due to center column)
    assert abs(score_p1 + score_p2) < 50  # Allow for small center column asymmetry


def test_bot_vs_minimax():
    """Test hybrid bot against minimax for a few moves."""
    from arena.minimax_bot import MinimaxBot
    
    hybrid = HybridBot(simulations=50)
    minimax = MinimaxBot(depth=4)
    game = ConnectFour()
    rng = random.Random(42)
    
    # Play 10 moves alternating
    for i in range(10):
        if game.winner is not None:
            break
        
        if i % 2 == 0:
            move = hybrid.choose_move(game, game.current_player, rng)
        else:
            move = minimax.choose_move(game, game.current_player, rng)
        
        game.drop(move)
    
    # Game should complete without error
    assert game.moves_played > 0
