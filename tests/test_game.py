from arena.game import ConnectFour


def play(game: ConnectFour, moves: list[int]) -> None:
    for col in moves:
        game.drop(col)


def test_horizontal_win() -> None:
    game = ConnectFour()
    play(game, [0, 0, 1, 1, 2, 2, 3])
    assert game.winner == 1
    assert game.is_terminal()


def test_vertical_win() -> None:
    game = ConnectFour()
    play(game, [0, 1, 0, 1, 0, 1, 0])
    assert game.winner == 1


def test_diagonal_win() -> None:
    game = ConnectFour()
    play(game, [0, 1, 1, 2, 2, 3, 2, 3, 3, 6, 3])
    assert game.winner == 1


def test_draw_when_board_full_without_possible_connect_n() -> None:
    game = ConnectFour(rows=4, cols=4, connect_n=5)
    for _ in range(game.rows):
        for col in range(game.cols):
            game.drop(col)
    assert game.winner == 0
    assert game.is_terminal()


def test_legal_moves_shrink_when_column_fills() -> None:
    game = ConnectFour(rows=3, cols=4, connect_n=3)
    assert 2 in game.legal_moves()
    game.drop(2)
    game.drop(2)
    game.drop(2)
    assert 2 not in game.legal_moves()
