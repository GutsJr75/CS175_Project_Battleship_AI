from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Set, Tuple

Coord = Tuple[int, int]


class ShotResult(str, Enum):
    MISS = "miss"
    HIT = "hit"
    SUNK = "sunk"


@dataclass(frozen=True)
class GameConfig:
    board_size: int = 10
    ship_sizes: Tuple[int, ...] = (5, 4, 3, 3, 2)


@dataclass
class Observation:
    board_size: int
    untried_cells: Set[Coord]
    past_moves: Dict[Coord, ShotResult]
    sunk_ship_sizes: Tuple[int, ...] = ()
    sunken_ship_coordinates: Tuple[Tuple[Coord, ...], ...] = ()


@dataclass
class GameStats:
    winner: str
    total_attacks: int
    hits: int
    misses: int
    sunk_ships: int
    ship_cells: int
    turns: int
    shot_history: Dict[Coord, ShotResult] = field(default_factory=dict)

    @property
    def hit_rate(self) -> float:
        if self.total_attacks == 0:
            return 0.0
        return self.hits / self.total_attacks
