from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .interfaces import Agent, PlacementStrategy
from .engine import run_single_game
from .types import GameConfig, GameStats


@dataclass
class BatchStats:
    games_played: int
    wins: int
    total_attacks: int
    total_hits: int
    total_misses: int
    average_attacks: float
    average_hit_rate: float
    average_runtime_seconds: float
    game_stats: List[GameStats] = field(default_factory=list)


def run_batch(
    agent: Agent,
    *,
    games: int,
    config: Optional[GameConfig] = None,
    placement_strategy: Optional[PlacementStrategy] = None,
    seed: Optional[int] = None,
    include_game_stats: bool = False,
) -> BatchStats:
    if games <= 0:
        raise ValueError("games must be positive.")

    rng = random.Random(seed)
    config = config or GameConfig()

    wins = 0
    total_attacks = 0
    total_hits = 0
    total_misses = 0
    runtimes: List[float] = []
    game_stats: List[GameStats] = []

    for _ in range(games):
        game_seed = rng.randrange(0, 10**9)
        start = time.perf_counter()
        stats = run_single_game(
            agent,
            config=config,
            placement_strategy=placement_strategy,
            seed=game_seed,
        )
        elapsed = time.perf_counter() - start
        runtimes.append(elapsed)

        wins += 1 if stats.winner == agent.name else 0
        total_attacks += stats.total_attacks
        total_hits += stats.hits
        total_misses += stats.misses
        if include_game_stats:
            game_stats.append(stats)

    average_attacks = total_attacks / games
    average_hit_rate = (total_hits / total_attacks) if total_attacks else 0.0
    average_runtime = sum(runtimes) / games

    return BatchStats(
        games_played=games,
        wins=wins,
        total_attacks=total_attacks,
        total_hits=total_hits,
        total_misses=total_misses,
        average_attacks=average_attacks,
        average_hit_rate=average_hit_rate,
        average_runtime_seconds=average_runtime,
        game_stats=game_stats,
    )


def format_game_stats(game_stats: Sequence[GameStats]) -> str:
    lines = []
    for game_number, stats in enumerate(game_stats, start=1):
        lines.append(
            "Game "
            f"{game_number}: attacks={stats.total_attacks}, "
            f"hits={stats.hits}, misses={stats.misses}"
        )
    return "\n".join(lines)


def format_verbose_game(game_stats: GameStats, *, game_number: int) -> str:
    lines = [f"Game {game_number} shot-by-shot:"]
    for shot_number, (coord, result) in enumerate(game_stats.shot_history.items(), start=1):
        lines.append(f"Shot {shot_number}: {coord} {result.value}")
    return "\n".join(lines)


def format_batch_stats(stats: BatchStats) -> str:
    return (
        f"Games played: {stats.games_played}\n"
        f"Wins: {stats.wins}\n"
        f"Total attacks: {stats.total_attacks}\n"
        f"Total hits: {stats.total_hits}\n"
        f"Total misses: {stats.total_misses}\n"
        f"Average attacks/game: {stats.average_attacks:.2f}\n"
        f"Average hit rate: {stats.average_hit_rate:.4f}\n"
        f"Average runtime/game: {stats.average_runtime_seconds:.6f}s"
    )
