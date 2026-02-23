"""Tests for all bot strategies."""

import random

import pytest

from arena.game import ConnectFour, PLAYER_ONE, PLAYER_TWO
from arena.bot import RandomBot, GreedyBot
from arena.minimax_bot import MinimaxBot
from arena.mcts_bot import MCTSBot
from arena.negamax_bot import NegamaxBot


class TestRandomBot:
    def test_returns_legal_move(self):
        game = ConnectFour()
        bot = RandomBot()
        rng = random.Random(42)
        move = bot.choose_move(game, PLAYER_ONE, rng)
        assert move in game.legal_moves()

    def test_plays_full_game_without_error(self):
        game = ConnectFour()
        bot = RandomBot()
        rng = random.Random(42)
        while not game.is_terminal():
            move = bot.choose_move(game, game.current_player, rng)
            game.drop(move)
        assert game.is_terminal()


class TestGreedyBot:
    def test_returns_legal_move(self):
        game = ConnectFour()
        bot = GreedyBot()
        rng = random.Random(42)
        move = bot.choose_move(game, PLAYER_ONE, rng)
        assert move in game.legal_moves()

    def test_takes_winning_move(self):
        game = ConnectFour()
        # Set up P1 with 3 in a row horizontally on bottom
        game.drop(0)  # P1
        game.drop(0)  # P2
        game.drop(1)  # P1
        game.drop(1)  # P2
        game.drop(2)  # P1
        game.drop(2)  # P2
        # P1 should take col 3 to win
        bot = GreedyBot()
        move = bot.choose_move(game, PLAYER_ONE, random.Random(0))
        assert move == 3

    def test_blocks_opponent_win(self):
        game = ConnectFour()
        # P2 has 3 in a row, P1 should block
        game.drop(0)  # P1 at (5,0)
        game.drop(1)  # P2 at (5,1)
        game.drop(6)  # P1 at (5,6)
        game.drop(2)  # P2 at (5,2)
        game.drop(6)  # P1 at (4,6)
        game.drop(3)  # P2 at (5,3) - three in a row, needs col 4
        # P2 has (5,1), (5,2), (5,3) - but wait, P1 should block col 4
        # Actually P1 is current player. P2 has 3 in row at bottom (cols 1,2,3)
        bot = GreedyBot()
        move = bot.choose_move(game, PLAYER_ONE, random.Random(0))
        assert move == 4  # block P2's win

    def test_plays_full_game_without_error(self):
        game = ConnectFour()
        bot = GreedyBot()
        rng = random.Random(42)
        while not game.is_terminal():
            move = bot.choose_move(game, game.current_player, rng)
            game.drop(move)
        assert game.is_terminal()


class TestMinimaxBot:
    def test_returns_legal_move(self):
        game = ConnectFour()
        bot = MinimaxBot(depth=2)
        rng = random.Random(42)
        move = bot.choose_move(game, PLAYER_ONE, rng)
        assert move in game.legal_moves()

    def test_takes_winning_move(self):
        game = ConnectFour()
        game.drop(0)  # P1
        game.drop(0)  # P2
        game.drop(1)  # P1
        game.drop(1)  # P2
        game.drop(2)  # P1
        game.drop(2)  # P2
        # P1 can win with col 3
        bot = MinimaxBot(depth=2)
        move = bot.choose_move(game, PLAYER_ONE, random.Random(0))
        assert move == 3

    def test_blocks_opponent_win(self):
        game = ConnectFour()
        game.drop(0)  # P1
        game.drop(1)  # P2
        game.drop(6)  # P1
        game.drop(2)  # P2
        game.drop(6)  # P1
        game.drop(3)  # P2 has 3 in row (cols 1,2,3)
        bot = MinimaxBot(depth=2)
        move = bot.choose_move(game, PLAYER_ONE, random.Random(0))
        assert move == 4  # block

    def test_beats_random_most_of_the_time(self):
        """Minimax should beat random in the majority of games."""
        wins = 0
        total = 10
        for seed in range(total):
            rng = random.Random(seed)
            game = ConnectFour()
            minimax = MinimaxBot(depth=4)
            rand_bot = RandomBot()
            bots = {PLAYER_ONE: minimax, PLAYER_TWO: rand_bot}
            while not game.is_terminal():
                bot = bots[game.current_player]
                move = bot.choose_move(game, game.current_player, rng)
                game.drop(move)
            if game.winner == PLAYER_ONE:
                wins += 1
        assert wins >= 7, f"Minimax only won {wins}/{total} against random"

    def test_plays_full_game_without_error(self):
        game = ConnectFour()
        bot = MinimaxBot(depth=3)
        rng = random.Random(42)
        while not game.is_terminal():
            move = bot.choose_move(game, game.current_player, rng)
            game.drop(move)
        assert game.is_terminal()


class TestMCTSBot:
    def test_returns_legal_move(self):
        game = ConnectFour()
        bot = MCTSBot(simulations=50)
        rng = random.Random(42)
        move = bot.choose_move(game, PLAYER_ONE, rng)
        assert move in game.legal_moves()

    def test_takes_winning_move(self):
        game = ConnectFour()
        game.drop(0)  # P1
        game.drop(0)  # P2
        game.drop(1)  # P1
        game.drop(1)  # P2
        game.drop(2)  # P1
        game.drop(2)  # P2
        bot = MCTSBot(simulations=100)
        move = bot.choose_move(game, PLAYER_ONE, random.Random(0))
        assert move == 3

    def test_beats_random_most_of_the_time(self):
        """MCTS should beat random in the majority of games."""
        wins = 0
        total = 10
        for seed in range(total):
            rng = random.Random(seed)
            game = ConnectFour()
            mcts = MCTSBot(simulations=100)
            rand_bot = RandomBot()
            bots = {PLAYER_ONE: mcts, PLAYER_TWO: rand_bot}
            while not game.is_terminal():
                bot = bots[game.current_player]
                move = bot.choose_move(game, game.current_player, rng)
                game.drop(move)
            if game.winner == PLAYER_ONE:
                wins += 1
        assert wins >= 7, f"MCTS only won {wins}/{total} against random"

    def test_plays_full_game_without_error(self):
        game = ConnectFour()
        bot = MCTSBot(simulations=50)
        rng = random.Random(42)
        while not game.is_terminal():
            move = bot.choose_move(game, game.current_player, rng)
            game.drop(move)
        assert game.is_terminal()


class TestNegamaxBot:
    def test_returns_legal_move(self):
        game = ConnectFour()
        bot = NegamaxBot(max_depth=4)
        rng = random.Random(42)
        move = bot.choose_move(game, PLAYER_ONE, rng)
        assert move in game.legal_moves()

    def test_takes_winning_move(self):
        game = ConnectFour()
        game.drop(0)  # P1
        game.drop(0)  # P2
        game.drop(1)  # P1
        game.drop(1)  # P2
        game.drop(2)  # P1
        game.drop(2)  # P2
        bot = NegamaxBot(max_depth=4)
        move = bot.choose_move(game, PLAYER_ONE, random.Random(0))
        assert move == 3

    def test_blocks_opponent_win(self):
        game = ConnectFour()
        game.drop(0)  # P1
        game.drop(0)  # P2
        game.drop(1)  # P1
        game.drop(1)  # P2
        game.drop(3)  # P1 (skip 2 to set up threat)
        bot = NegamaxBot(max_depth=4)
        move = bot.choose_move(game, PLAYER_TWO, random.Random(0))
        assert move == 2  # Must block P1 from winning

    def test_beats_random_most_of_the_time(self):
        """Negamax should beat random in the majority of games."""
        wins = 0
        total = 10
        for seed in range(total):
            rng = random.Random(seed)
            game = ConnectFour()
            negamax = NegamaxBot(max_depth=4)
            rand_bot = RandomBot()
            bots = {PLAYER_ONE: negamax, PLAYER_TWO: rand_bot}
            while not game.is_terminal():
                bot = bots[game.current_player]
                move = bot.choose_move(game, game.current_player, rng)
                game.drop(move)
            if game.winner == PLAYER_ONE:
                wins += 1
        assert wins >= 8, f"Negamax only won {wins}/{total} against random"

    def test_beats_greedy(self):
        """Negamax should consistently beat greedy."""
        wins = 0
        total = 10
        for seed in range(total):
            rng = random.Random(seed)
            game = ConnectFour()
            negamax = NegamaxBot(max_depth=4)
            greedy = GreedyBot()
            bots = {PLAYER_ONE: negamax, PLAYER_TWO: greedy}
            while not game.is_terminal():
                bot = bots[game.current_player]
                move = bot.choose_move(game, game.current_player, rng)
                game.drop(move)
            if game.winner == PLAYER_ONE:
                wins += 1
        assert wins >= 7, f"Negamax only won {wins}/{total} against greedy"

    def test_plays_full_game_without_error(self):
        game = ConnectFour()
        bot = NegamaxBot(max_depth=4)
        rng = random.Random(42)
        while not game.is_terminal():
            move = bot.choose_move(game, game.current_player, rng)
            game.drop(move)
        assert game.is_terminal()

    def test_different_depths(self):
        """Test that different depths still produce legal moves."""
        game = ConnectFour()
        for depth in [1, 2, 4, 6]:
            bot = NegamaxBot(max_depth=depth)
            move = bot.choose_move(game, PLAYER_ONE, random.Random(42))
            assert move in game.legal_moves(), f"Depth {depth} produced illegal move"

    def test_prefers_center_early(self):
        """Negamax should prefer center column in early game."""
        game = ConnectFour()
        bot = NegamaxBot(max_depth=6)
        move = bot.choose_move(game, PLAYER_ONE, random.Random(42))
        # Center columns are 2, 3, 4 (0-indexed, 7 columns total)
        assert move in [2, 3, 4], f"Expected center column, got {move}"
