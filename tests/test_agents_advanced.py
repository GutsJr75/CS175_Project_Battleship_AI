from __future__ import annotations

from battleship.agent_checkerboard import CheckerboardAgent
from battleship.agent_heatmap import ProbabilityHeatmapAgent
from battleship.engine import run_single_game
from battleship.types import GameConfig, Observation, ShotResult


def make_observation(
    board_size: int,
    past_moves: dict[tuple[int, int], ShotResult] | None = None,
) -> Observation:
    past_moves = past_moves or {}
    all_cells = {
        (row, col)
        for row in range(board_size)
        for col in range(board_size)
    }
    return Observation(
        board_size=board_size,
        untried_cells=all_cells - set(past_moves),
        past_moves=past_moves,
        sunk_ship_sizes=(),
    )


def test_checkerboard_agent_starts_on_checkerboard_cell() -> None:
    agent = CheckerboardAgent()
    observation = make_observation(4)

    shot = agent.select_shot(observation)

    assert (shot[0] + shot[1]) % 2 == 0


def test_checkerboard_agent_targets_neighbors_after_hit() -> None:
    agent = CheckerboardAgent()
    agent.on_shot_result((1, 1), ShotResult.HIT)
    observation = make_observation(4, {(1, 1): ShotResult.HIT})

    shot = agent.select_shot(observation)

    assert shot in {(0, 1), (2, 1), (1, 0), (1, 2)}


def test_checkerboard_agent_continues_same_row_after_two_hits() -> None:
    agent = CheckerboardAgent()
    agent.on_shot_result((2, 2), ShotResult.HIT)
    agent.on_shot_result((2, 3), ShotResult.HIT)
    observation = make_observation(
        6,
        {
            (2, 2): ShotResult.HIT,
            (2, 3): ShotResult.HIT,
        },
    )

    shot = agent.select_shot(observation)

    assert shot in {(2, 1), (2, 4)}


def test_checkerboard_agent_clears_active_hits_after_sunk() -> None:
    agent = CheckerboardAgent()
    agent.on_shot_result((1, 1), ShotResult.HIT)
    agent.on_shot_result((1, 2), ShotResult.SUNK)
    observation = make_observation(
        4,
        {
            (1, 1): ShotResult.HIT,
            (1, 2): ShotResult.SUNK,
        },
    )

    shot = agent.select_shot(observation)

    assert shot == (0, 0)


def test_probability_heatmap_agent_prefers_cells_consistent_with_hit() -> None:
    agent = ProbabilityHeatmapAgent(ship_sizes=(3,))
    agent.on_shot_result((2, 2), ShotResult.HIT)
    observation = make_observation(5, {(2, 2): ShotResult.HIT})

    shot = agent.select_shot(observation)

    assert shot[0] == 2 or shot[1] == 2
    assert shot != (2, 2)


def test_probability_heatmap_agent_does_not_repeat_or_shoot_outside_board() -> None:
    agent = ProbabilityHeatmapAgent(ship_sizes=(2,))
    past_moves = {
        (0, 0): ShotResult.MISS,
        (1, 1): ShotResult.MISS,
    }
    observation = make_observation(3, past_moves)

    shot = agent.select_shot(observation)

    assert shot not in past_moves
    assert 0 <= shot[0] < observation.board_size
    assert 0 <= shot[1] < observation.board_size


def test_probability_heatmap_agent_removes_sunk_ship_sizes() -> None:
    agent = ProbabilityHeatmapAgent(ship_sizes=(2, 3))

    assert agent._remaining_ship_sizes((3,)) == [2]


def test_new_agents_complete_full_games() -> None:
    config = GameConfig()

    for agent in (CheckerboardAgent(), ProbabilityHeatmapAgent()):
        stats = run_single_game(agent, config=config, seed=1001)

        assert stats.total_attacks <= config.board_size * config.board_size
        assert stats.hits == sum(config.ship_sizes)
        assert stats.hits + stats.misses == stats.total_attacks
