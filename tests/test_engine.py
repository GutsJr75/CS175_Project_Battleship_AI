from __future__ import annotations

import random
import pytest

from battleship.engine import BattleshipGame, RandomPlacementStrategy
from battleship.types import GameConfig, ShotResult


def test_random_placement_produces_legal_fleet() -> None:
    config = GameConfig()
    strategy = RandomPlacementStrategy()
    fleet = strategy.place_ships(
        config.board_size, list(config.ship_sizes), rng=random.Random(7)
    )

    assert len(fleet) == len(config.ship_sizes)
    occupied = set()
    for ship_cells, expected_size in zip(fleet, config.ship_sizes):
        assert len(ship_cells) == expected_size
        for row, col in ship_cells:
            assert 0 <= row < config.board_size
            assert 0 <= col < config.board_size
            assert (row, col) not in occupied
            occupied.add((row, col))


def test_fire_hit_miss_and_sunk_flow() -> None:
    config = GameConfig(board_size=5, ship_sizes=(2,))
    game = BattleshipGame(config=config, ship_positions=[{(1, 1), (1, 2)}])

    assert game.fire((0, 0)) == ShotResult.MISS
    assert game.fire((1, 1)) == ShotResult.HIT
    assert game.fire((1, 2)) == ShotResult.SUNK
    assert game.is_game_over is True


def test_duplicate_shot_raises_error() -> None:
    config = GameConfig(board_size=5, ship_sizes=(2,))
    game = BattleshipGame(config=config, ship_positions=[{(1, 1), (1, 2)}])

    game.fire((0, 0))
    with pytest.raises(ValueError):
        game.fire((0, 0))


def test_constructor_rejects_overlap() -> None:
    config = GameConfig(board_size=5, ship_sizes=(2, 2))
    with pytest.raises(ValueError):
        BattleshipGame(
            config=config,
            ship_positions=[{(0, 0), (0, 1)}, {(0, 1), (0, 2)}],
        )


def test_constructor_rejects_out_of_bounds() -> None:
    config = GameConfig(board_size=5, ship_sizes=(2,))
    with pytest.raises(ValueError):
        BattleshipGame(config=config, ship_positions=[{(5, 0), (5, 1)}])
