from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Set

from .types import Coord, Observation, ShotResult


@dataclass
class ProbabilityHeatmapAgent:
    ship_sizes: tuple[int, ...] = (5, 4, 3, 3, 2)
    name: str = "Agent 3 - Probability Heatmap"
    _attempted: Set[Coord] = field(default_factory=set, init=False)
    _active_hits: Set[Coord] = field(default_factory=set, init=False)
    _resolved_hits: Set[Coord] = field(default_factory=set, init=False)

    def reset(self) -> None:
        self._attempted.clear()
        self._active_hits.clear()
        self._resolved_hits.clear()

    def select_shot(self, observation: Observation) -> Coord:
        self._attempted.update(observation.past_moves)
        candidates = {
            coord
            for coord in observation.untried_cells - self._attempted
            if self._in_bounds(coord, observation.board_size)
        }
        if not candidates:
            raise ValueError("No legal cells left for probability heatmap agent.")

        heatmap = self._build_heatmap(observation, candidates)
        return max(sorted(candidates), key=lambda coord: heatmap.get(coord, 0))

    def on_shot_result(self, coord: Coord, result: ShotResult) -> None:
        self._attempted.add(coord)
        if result == ShotResult.HIT:
            self._active_hits.add(coord)
        elif result == ShotResult.SUNK:
            self._resolved_hits.update(self._active_hits)
            self._resolved_hits.add(coord)
            self._active_hits.clear()

    def _build_heatmap(
        self, observation: Observation, candidates: Set[Coord]
    ) -> dict[Coord, int]:
        remaining_sizes = self._remaining_ship_sizes(observation.sunk_ship_sizes)
        heatmap = {coord: 0 for coord in candidates}
        placements = []
        blocked = set(observation.past_moves) - self._active_hits
        blocked.update(self._resolved_hits)

        for ship_size in remaining_sizes:
            for placement in self._placements(observation.board_size, ship_size):
                if placement & blocked:
                    continue
                hit_count = len(placement & self._active_hits)
                placements.append((placement, hit_count))

        best_hit_count = max((hit_count for _, hit_count in placements), default=0)
        if best_hit_count:
            selected = [
                (placement, hit_count)
                for placement, hit_count in placements
                if hit_count == best_hit_count
            ]
        else:
            selected = placements

        for placement, hit_count in selected:
            weight = 1 + hit_count * 4
            for coord in placement:
                if coord in candidates:
                    heatmap[coord] += weight

        return heatmap

    def _remaining_ship_sizes(self, sunk_ship_sizes: Iterable[int]) -> list[int]:
        counts = Counter(self.ship_sizes)
        for ship_size in sunk_ship_sizes:
            if counts[ship_size] > 0:
                counts[ship_size] -= 1
        return sorted(counts.elements(), reverse=True)

    def _placements(self, board_size: int, ship_size: int) -> Iterable[Set[Coord]]:
        if ship_size > board_size:
            return

        for row in range(board_size):
            for col in range(board_size - ship_size + 1):
                yield {(row, col + offset) for offset in range(ship_size)}

        for row in range(board_size - ship_size + 1):
            for col in range(board_size):
                yield {(row + offset, col) for offset in range(ship_size)}

    def _in_bounds(self, coord: Coord, board_size: int) -> bool:
        row, col = coord
        return 0 <= row < board_size and 0 <= col < board_size
