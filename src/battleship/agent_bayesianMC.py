from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Optional, Set, Tuple

from .types import Coord, Observation, ShotResult


@dataclass
class BayesianMCAgent:
    """
    Agent 4: Bayesian Search Theory using Monte Carlo sampling

    This agent treats each complete remaining fleet arrangement as a hypothesis.
    After every observation, it builds a posterior sample of full-board
    configurations that are consistent with the known misses, active hits, and
    sunk ships. It then shoots the untried cell that appears most often across
    those valid configurations.

    The exact Bayesian version would enumerate every valid complete board. That
    can be expensive, so this implementation enumerates/samples up to
    max_configurations valid boards and uses those boards to approximate the
    posterior probability map.
    """

    ship_sizes: tuple[int, ...] = (5, 4, 3, 3, 2)
    name: str = "Agent 5 - Bayesian Search"
    max_configurations: int = 750
    seed: Optional[int] = None
    
    # store a copy of the attempted, active, and resolved hits.
    _attempted: Set[Coord] = field(default_factory=set, init=False) 
    _active_hits: Set[Coord] = field(default_factory=set, init=False)
    _resolved_hits: Set[Coord] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def reset(self) -> None:
        self._attempted.clear()
        self._active_hits.clear()
        self._resolved_hits.clear()

    def select_shot(self, observation: Observation) -> Coord:
        self._attempted.update(observation.past_moves)
        self._update_active_resolved_hits(observation)                    

        posterior_scores = self._build_posterior_scores(observation)
        
        return max(sorted(observation.untried_cells), key=lambda coord: posterior_scores.get(coord, 0))


    def on_shot_result(self, coord: Coord, result: ShotResult) -> None:
        self._attempted.add(coord)

    def _build_posterior_scores(self, observation: Observation) -> dict[Coord, int]:
        # Sample valid world configurations given the current information
        # Based on the sampled worlds, generate a probability function for the most likeley tile
        # return that pdf
        worlds = self._sample_valid_worlds(observation)

        scores: dict[Coord, int] = {
            coord: 0
            for coord in observation.untried_cells
        }

        for world in worlds:
            for coord in world:
                if coord in scores:
                    scores[coord] += 1

        return scores
    
    def _sample_valid_worlds(self, observation: Observation) -> list[set[Coord]]:
        """        
        Generate up to self.max_configurations valid complete remaining-board configurations.

        Each sampled world is a set of coordinates occupied by all remaining, unsunk ships.

        A valid world must:
            1. avoid known misses,
            2. avoid resolved sunk ship cells,
            3. cover every active unresolved hit,
            4. place all remaining ships without overlap.

        How the sampler works:
            1. For all remaining ship sizes, computes the legal individual ship placements
            2. Shuffle remaining ship length
            3. For each ship:
                Randomly choose a valid placement that doesn't overlap
            
        """
        board_size = observation.board_size

        # Cells that were shot and were not hits/sunk are known misses.
        misses = {
            coord
            for coord, result in observation.past_moves.items()
            if result == ShotResult.MISS
        }

        active_hits = set(self._active_hits)
        resolved_hits = set(self._resolved_hits)

        # Remove sunk ships from the fleet.
        remaining_ship_sizes = list(self.ship_sizes)
        for sunk_size in observation.sunk_ship_sizes:
            if sunk_size in remaining_ship_sizes:
                remaining_ship_sizes.remove(sunk_size)

        if not remaining_ship_sizes:
            return []

        # Precompute all legal individual placements for each remaining ship size.
        # Placements only avoid known misses and resolved sunk ships.
        placements_by_size: dict[int, list[set[Coord]]] = {}
        blocked = misses | resolved_hits

        for ship_size in set(remaining_ship_sizes):
            placements = []

            # Horizontal placements.
            for row in range(board_size):
                for col_start in range(board_size - ship_size + 1):
                    placement = {
                        (row, col_start + offset)
                        for offset in range(ship_size)
                    }

                    if placement & blocked:
                        continue

                    placements.append(placement)

            # Vertical placements.
            for row_start in range(board_size - ship_size + 1):
                for col in range(board_size):
                    placement = {
                        (row_start + offset, col)
                        for offset in range(ship_size)
                    }

                    if placement & blocked:
                        continue

                    placements.append(placement)

            placements_by_size[ship_size] = placements



        valid_worlds: list[set[Coord]] = []

        max_attempts = self.max_configurations * 50

        for _ in range(max_attempts):
            if len(valid_worlds) >= self.max_configurations:
                break

            occupied: set[Coord] = set()
            valid = True

            # Shuffle ship order so repeated lengths, like the two length-3 ships,
            # do not always get placed in the same deterministic order.
            ship_order = list(remaining_ship_sizes)
            self._rng.shuffle(ship_order)

            for ship_size in ship_order:
                possible_placements = placements_by_size.get(ship_size, [])

                if not possible_placements:
                    valid = False
                    break

                # Try placements in randomized order.
                shuffled_placements = list(possible_placements)
                self._rng.shuffle(shuffled_placements)

                chosen_placement = None

                for placement in shuffled_placements:
                    # Ships cannot overlap each other.
                    if placement & occupied:
                        continue

                    chosen_placement = placement
                    break

                if chosen_placement is None:
                    valid = False
                    break

                occupied.update(chosen_placement)

            if not valid:
                continue

            if not active_hits.issubset(occupied):
                continue

            valid_worlds.append(occupied)

        return valid_worlds



    def _update_active_resolved_hits(self, observation: Observation) -> set[Coord]:
        all_hit_cells = {
            coord
            for coord, result in observation.past_moves.items()
            if result in (ShotResult.HIT, ShotResult.SUNK)
        }

        resolved_hits = {
            coord
            for ship in observation.sunken_ship_coordinates
            for coord in ship
        }
        self._resolved_hits = resolved_hits

        self._active_hits = all_hit_cells - resolved_hits

    def _in_bounds(self, coord: Coord, board_size: int) -> bool:
        row, col = coord
        return 0 <= row < board_size and 0 <= col < board_size