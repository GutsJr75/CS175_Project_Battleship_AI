from __future__ import annotations

from battleship.agent_random import RandomAgent
from battleship.simulation import (
    format_game_stats,
    format_verbose_game,
    run_batch,
)


def test_batch_stats_are_consistent() -> None:
    stats = run_batch(RandomAgent(seed=21), games=20, seed=123)

    assert stats.games_played == 20
    assert stats.total_hits == 20 * 17
    assert stats.total_attacks == stats.total_hits + stats.total_misses
    assert 0.0 < stats.average_hit_rate <= 1.0
    assert stats.average_attacks > 0
    assert stats.average_runtime_seconds >= 0.0


def test_seeded_batch_is_reproducible_on_core_metrics() -> None:
    first = run_batch(RandomAgent(seed=999), games=25, seed=777)
    second = run_batch(RandomAgent(seed=999), games=25, seed=777)

    assert first.games_played == second.games_played
    assert first.wins == second.wins
    assert first.total_attacks == second.total_attacks
    assert first.total_hits == second.total_hits
    assert first.total_misses == second.total_misses
    assert first.average_attacks == second.average_attacks
    assert first.average_hit_rate == second.average_hit_rate


def test_batch_can_include_per_game_stats() -> None:
    stats = run_batch(RandomAgent(seed=12), games=3, seed=55, include_game_stats=True)

    assert len(stats.game_stats) == 3
    assert sum(game.total_attacks for game in stats.game_stats) == stats.total_attacks
    assert sum(game.hits for game in stats.game_stats) == stats.total_hits
    assert all(game.hits == 17 for game in stats.game_stats)


def test_format_game_stats_renders_one_line_per_game() -> None:
    stats = run_batch(RandomAgent(seed=2), games=2, seed=90, include_game_stats=True)

    output = format_game_stats(stats.game_stats)

    assert "Game 1:" in output
    assert "Game 2:" in output
    assert "hits=17" in output


def test_format_verbose_game_includes_shot_results() -> None:
    stats = run_batch(RandomAgent(seed=3), games=1, seed=10, include_game_stats=True)

    output = format_verbose_game(stats.game_stats[0], game_number=1)

    assert "Game 1 shot-by-shot:" in output
    assert "Shot 1:" in output
    assert any(result in output for result in ("miss", "hit", "sunk"))
