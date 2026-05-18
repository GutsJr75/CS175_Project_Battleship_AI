from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from .interfaces import Agent, PlacementStrategy
from .types import Coord, GameConfig, GameStats, Observation, ShotResult


@dataclass
class RandomPlacementStrategy:
    """Places ships randomly with classic Battleship legality rules."""

    def place_ships(
        self, board_size: int, ship_sizes: List[int], rng: random.Random
    ) -> List[Set[Coord]]:
        occupied: Set[Coord] = set()
        fleet: List[Set[Coord]] = []

        for ship_size in ship_sizes:
            placed = False
            while not placed:
                horizontal = rng.choice([True, False])
                if horizontal:
                    row = rng.randrange(board_size)
                    col = rng.randrange(board_size - ship_size + 1)
                    ship_cells = {(row, col + offset) for offset in range(ship_size)}
                else:
                    row = rng.randrange(board_size - ship_size + 1)
                    col = rng.randrange(board_size)
                    ship_cells = {(row + offset, col) for offset in range(ship_size)}

                if ship_cells & occupied:
                    continue

                occupied.update(ship_cells)
                fleet.append(ship_cells)
                placed = True

        return fleet


class BattleshipGame:
    def __init__(self, config: GameConfig, ship_positions: List[Set[Coord]]) -> None:
        self.config = config
        self.ship_positions = ship_positions
        self.attacked_cells: Set[Coord] = set()
        self.sunk_ship_sizes: List[int] = []
        self.sunken_ship_coordinates: List[Set[Coord]] = []
        self._validate_ship_positions()

        self._coord_to_ship_index: Dict[Coord, int] = {}
        for ship_index, ship in enumerate(self.ship_positions):
            for coord in ship:
                self._coord_to_ship_index[coord] = ship_index

        self._remaining_ship_cells: Dict[int, Set[Coord]] = {
            index: set(ship) for index, ship in enumerate(self.ship_positions)
        }

    def _validate_ship_positions(self) -> None:
        if len(self.ship_positions) != len(self.config.ship_sizes):
            raise ValueError("Number of ships does not match config ship sizes.")

        all_cells: Set[Coord] = set()
        for expected_size, ship_cells in zip(self.config.ship_sizes, self.ship_positions):
            if len(ship_cells) != expected_size:
                raise ValueError(
                    f"Ship has size {len(ship_cells)}, expected {expected_size}."
                )

            for row, col in ship_cells:
                if not self._in_bounds((row, col)):
                    raise ValueError(f"Ship coordinate {(row, col)} out of bounds.")
                if (row, col) in all_cells:
                    raise ValueError("Ships overlap.")
                all_cells.add((row, col))

            rows = {r for r, _ in ship_cells}
            cols = {c for _, c in ship_cells}
            if len(rows) > 1 and len(cols) > 1:
                raise ValueError("Ships must be straight (horizontal or vertical).")

            # Ensure the ship occupies contiguous cells in its line.
            if len(rows) == 1:
                ordered = sorted(col for _, col in ship_cells)
            else:
                ordered = sorted(row for row, _ in ship_cells)

            for i in range(len(ordered) - 1):
                if ordered[i + 1] != ordered[i] + 1:
                    raise ValueError("Ship cells must be contiguous.")

    def _in_bounds(self, coord: Coord) -> bool:
        row, col = coord
        return 0 <= row < self.config.board_size and 0 <= col < self.config.board_size

    @property
    def is_game_over(self) -> bool:
        return len(self.sunk_ship_sizes) == len(self.config.ship_sizes)

    def available_cells(self) -> Set[Coord]:
        all_cells = {
            (row, col)
            for row in range(self.config.board_size)
            for col in range(self.config.board_size)
        }
        return all_cells - self.attacked_cells

    def fire(self, coord: Coord) -> ShotResult:
        if not self._in_bounds(coord):
            raise ValueError(f"Shot {coord} is out of bounds.")
        if coord in self.attacked_cells:
            raise ValueError(f"Shot {coord} was already attempted.")

        self.attacked_cells.add(coord)
        ship_index = self._coord_to_ship_index.get(coord)

        if ship_index is None:
            return ShotResult.MISS

        remaining = self._remaining_ship_cells[ship_index]
        remaining.remove(coord)

        if len(remaining) == 0:
            sunk_ship = set(self.ship_positions[ship_index])
            sunk_size = len(sunk_ship)
            self.sunk_ship_sizes.append(sunk_size)
            self.sunken_ship_coordinates.append(sunk_ship)
            return ShotResult.SUNK

        return ShotResult.HIT


def run_single_game(
    agent: Agent,
    *,
    config: Optional[GameConfig] = None,
    placement_strategy: Optional[PlacementStrategy] = None,
    seed: Optional[int] = None,
) -> GameStats:
    config = config or GameConfig()
    placement_strategy = placement_strategy or RandomPlacementStrategy()
    rng = random.Random(seed)

    ships = placement_strategy.place_ships(config.board_size, list(config.ship_sizes), rng)
    game = BattleshipGame(config=config, ship_positions=ships)

    agent.reset()
    history: Dict[Coord, ShotResult] = {}

    while not game.is_game_over:
        observation = Observation(
            board_size=config.board_size,
            untried_cells=game.available_cells(),
            past_moves=dict(history),
            sunk_ship_sizes=tuple(game.sunk_ship_sizes),
            sunken_ship_coordinates=tuple(
                tuple(sorted(ship)) for ship in game.sunken_ship_coordinates
            ),
        )

        shot = agent.select_shot(observation)
        result = game.fire(shot)
        agent.on_shot_result(shot, result)
        history[shot] = result

    hit_count = sum(1 for value in history.values() if value in (ShotResult.HIT, ShotResult.SUNK))
    miss_count = sum(1 for value in history.values() if value == ShotResult.MISS)

    return GameStats(
        winner=agent.name,
        total_attacks=len(history),
        hits=hit_count,
        misses=miss_count,
        sunk_ships=len(game.sunk_ship_sizes),
        ship_cells=sum(config.ship_sizes),
        turns=len(history),
        shot_history=history,
    )
