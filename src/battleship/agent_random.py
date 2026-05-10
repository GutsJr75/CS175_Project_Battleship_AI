from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional, Set

from .types import Coord, Observation, ShotResult


@dataclass
class RandomAgent:
    """Agent 1: pure random guessing over untried cells."""

    seed: Optional[int] = None
    name: str = "Agent 1 - Random Guessing"
    _attempted: Set[Coord] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def reset(self) -> None:
        self._attempted.clear()

    def select_shot(self, observation: Observation) -> Coord:
        candidates = list(observation.untried_cells - self._attempted)
        if not candidates:
            raise ValueError("No legal cells left for random agent.")
        return self._rng.choice(candidates)

    def on_shot_result(self, coord: Coord, result: ShotResult) -> None:
        del result  # Random agent does not use feedback.
        self._attempted.add(coord)
