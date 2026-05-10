from __future__ import annotations

import random
from typing import List, Protocol, Set

from .types import Coord, Observation, ShotResult


class Agent(Protocol):
    name: str

    def reset(self) -> None:
        ...

    def select_shot(self, observation: Observation) -> Coord:
        ...

    def on_shot_result(self, coord: Coord, result: ShotResult) -> None:
        ...


class PlacementStrategy(Protocol):
    def place_ships(
        self, board_size: int, ship_sizes: List[int], rng: random.Random
    ) -> List[Set[Coord]]:
        ...
