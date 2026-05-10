from __future__ import annotations

from battleship.agent_random import RandomAgent
from battleship.engine import run_single_game
from battleship.types import GameConfig, Observation, ShotResult


def test_random_agent_selects_only_untried_cells() -> None:
    agent = RandomAgent(seed=11)
    observation = Observation(
        board_size=3,
        untried_cells={(0, 0), (0, 1), (1, 1)},
        past_moves={},
        sunk_ship_sizes=(),
    )

    shot = agent.select_shot(observation)
    assert shot in observation.untried_cells


def test_random_agent_does_not_repeat_shots_when_state_updates() -> None:
    agent = RandomAgent(seed=5)
    all_cells = {(0, 0), (0, 1), (1, 0), (1, 1)}
    seen = set()

    for _ in range(4):
        observation = Observation(
            board_size=2,
            untried_cells=all_cells - seen,
            past_moves={coord: ShotResult.MISS for coord in seen},
            sunk_ship_sizes=(),
        )
        shot = agent.select_shot(observation)
        assert shot not in seen
        agent.on_shot_result(shot, ShotResult.MISS)
        seen.add(shot)

    assert seen == all_cells


def test_random_agent_completes_a_full_game() -> None:
    agent = RandomAgent(seed=13)
    config = GameConfig()
    stats = run_single_game(agent, config=config, seed=1001)

    assert stats.total_attacks <= config.board_size * config.board_size
    assert stats.hits == sum(config.ship_sizes)
    assert stats.hits + stats.misses == stats.total_attacks
