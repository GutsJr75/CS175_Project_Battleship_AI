from __future__ import annotations

import argparse
from .agent_bayesianMC import BayesianMCAgent
from .agent_checkerboard import CheckerboardAgent
from .agent_heatmap import ProbabilityHeatmapAgent
from .agent_random import RandomAgent
from .simulation import (
    format_batch_stats,
    format_game_stats,
    format_verbose_game,
    run_batch,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Battleship AI simulations.")
    parser.add_argument(
        "--agent",
        choices=("random", "checkerboard", "heatmap", "bayesian_mc"),
        default="random",
        help="Agent strategy to run.",
    )
    parser.add_argument("--games", type=int, default=100, help="Number of games to run.")
    parser.add_argument("--seed", type=int, default=42, help="Seed for reproducible runs.")
    parser.add_argument(
        "--per-game",
        action="store_true",
        help="Print one summary line for each simulated game.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print every shot for each simulated game. Best for small runs.",
    )
    args = parser.parse_args()

    agents = {
        "random": RandomAgent(seed=args.seed),
        "checkerboard": CheckerboardAgent(),
        "heatmap": ProbabilityHeatmapAgent(),
        "bayesian_mc": BayesianMCAgent()
    }
    agent = agents[args.agent]
    stats = run_batch(
        agent,
        games=args.games,
        seed=args.seed,
        include_game_stats=args.per_game or args.verbose,
    )
    if args.per_game and stats.game_stats:
        print(format_game_stats(stats.game_stats))
    if args.verbose and stats.game_stats:
        if args.per_game:
            print()
        print("\n\n".join(
            format_verbose_game(game_stats, game_number=index)
            for index, game_stats in enumerate(stats.game_stats, start=1)
        ))
        print()
    print(format_batch_stats(stats))


if __name__ == "__main__":
    main()
