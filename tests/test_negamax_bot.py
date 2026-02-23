"""Tests for the NegamaxBot — strongest bot in the arena."""

import random

import pytest

from arena.game import ConnectFour, PLAYER_ONE, PLAYER_TWO
from arena.negamax_bot import NegamaxBot
from arena.bot import RandomBot
from arena.minimax_bot import MinimaxBot


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
        # P1 can win with col 3
        bot = NegamaxBot(max_depth=2)
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
        bot = NegamaxBot(max_depth=2)
        move = bot.choose_move(game, PLAYER_ONE, random.Random(0))
        assert move == 4  # block

    def test_beats_random_consistently(self):
        """Negamax should beat random in nearly every game."""
        wins = 0
        total = 10
        for seed in range(total):
            rng = random.Random(seed)
            game = ConnectFour()
            negamax = NegamaxBot(max_depth=6)
            rand_bot = RandomBot()
            bots = {PLAYER_ONE: negamax, PLAYER_TWO: rand_bot}
            while not game.is_terminal():
                bot = bots[game.current_player]
                move = bot.choose_move(game, game.current_player, rng)
                game.drop(move)
            if game.winner == PLAYER_ONE:
                wins += 1
        assert wins >= 9, f"Negamax only won {wins}/{total} against random"

    def test_plays_full_game_without_error(self):
        game = ConnectFour()
        bot = NegamaxBot(max_depth=4)
        rng = random.Random(42)
        while not game.is_terminal():
            move = bot.choose_move(game, game.current_player, rng)
            game.drop(move)
        assert game.is_terminal()

    def test_reproducible_with_same_seed(self):
        """Same seed should produce same moves."""
        moves_a = []
        moves_b = []
        for run_moves in (moves_a, moves_b):
            game = ConnectFour()
            bot = NegamaxBot(max_depth=4)
            rng = random.Random(99)
            for _ in range(6):
                if game.is_terminal():
                    break
                move = bot.choose_move(game, game.current_player, rng)
                run_moves.append(move)
                game.drop(move)
        assert moves_a == moves_b

    def test_handles_nearly_full_board(self):
        """Should not crash when few moves remain."""
        game = ConnectFour()
        rng = random.Random(42)
        rand_bot = RandomBot()
        # Play most of the game randomly
        while not game.is_terminal() and game.moves_played < 38:
            move = rand_bot.choose_move(game, game.current_player, rng)
            game.drop(move)
        if not game.is_terminal():
            bot = NegamaxBot(max_depth=10)
            move = bot.choose_move(game, game.current_player, rng)
            assert move in game.legal_moves()
