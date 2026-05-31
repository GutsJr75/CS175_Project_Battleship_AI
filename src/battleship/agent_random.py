from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional, Set

from .types import Coord, Observation, ShotResult


@dataclass
class RandomAgent:
    """Agent 1: random guessing over untried cells until it lands a hit,
    after which it tries to sink the entire ship before proceeding to random
    guessing again"""

    seed: Optional[int] = None
    name: str = "Agent 1 - Random Guessing"
    _attempted: Set[Coord] = field(default_factory=set, init=False)
    _active_hits: Set[Coord] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def reset(self) -> None:
        self._attempted.clear()
        self._active_hits.clear()

    def select_shot(self, observation: Observation) -> Coord:
        self._attempted.update(observation.past_moves)

        candidates = list(observation.untried_cells - self._attempted)
        if not candidates:
            raise ValueError("No legal cells left for random agent.")

        target_candidates = self._get_target_candidates(observation, set(candidates))

        if target_candidates:
            return self._rng.choice(sorted(target_candidates))

        return self._rng.choice(candidates)
    
    def on_shot_result(self, coord: Coord, result: ShotResult) -> None:
        self._attempted.add(coord)

        if result == ShotResult.HIT:
            self._active_hits.add(coord)

        elif result == ShotResult.SUNK:
            self._active_hits.clear()

    def _get_target_candidates(
        self,
        observation: Observation,
        candidates: set[Coord],
    ) -> list[Coord]:
        """
        Upon landing a hit: If there is one active hit, try its four neighbors.
        If there are multiple active hits in the same row or column, continue
        along that line from either end.
        """

        active_hits = {
            coord
            for coord in self._active_hits
            if coord not in self._attempted or observation.past_moves.get(coord) in {ShotResult.HIT, ShotResult.SUNK}
        }

        if not active_hits:
            return []

        # Multiple hits in the same row imply a horizontal ship.
        rows = {row for row, _ in active_hits}
        cols = {col for _, col in active_hits}

        if len(active_hits) >= 2 and len(rows) == 1:
            row = next(iter(rows))
            hit_cols = sorted(col for _, col in active_hits)
            line_candidates = {
                (row, hit_cols[0] - 1),
                (row, hit_cols[-1] + 1),
            }
            return [coord for coord in line_candidates if coord in candidates]

        # Multiple hits in the same column imply a vertical ship.
        if len(active_hits) >= 2 and len(cols) == 1:
            col = next(iter(cols))
            hit_rows = sorted(row for row, _ in active_hits)
            line_candidates = {
                (hit_rows[0] - 1, col),
                (hit_rows[-1] + 1, col),
            }
            return [coord for coord in line_candidates if coord in candidates]

        # If there is only one hit, or hits are not aligned, try all neighbors.
        neighbors: set[Coord] = set()
        for row, col in active_hits:
            neighbors.update(
                {
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                }
            )

        return [coord for coord in neighbors if coord in candidates]
