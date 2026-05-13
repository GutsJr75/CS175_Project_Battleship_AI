from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set

from .types import Coord, Observation, ShotResult


@dataclass
class CheckerboardAgent:
    name: str = "Agent 2 - Checkerboard"
    _attempted: Set[Coord] = field(default_factory=set, init=False)
    _active_hits: Set[Coord] = field(default_factory=set, init=False)

    def reset(self) -> None:
        self._attempted.clear()
        self._active_hits.clear()

    def select_shot(self, observation: Observation) -> Coord:
        self._attempted.update(observation.past_moves)
        candidates = {
            coord
            for coord in observation.untried_cells - self._attempted
            if self._in_bounds(coord, observation.board_size)
        }
        if not candidates:
            raise ValueError("No legal cells left for checkerboard agent.")

        target = self._select_local_target(observation.board_size, candidates)
        if target is not None:
            return target

        checkerboard = [
            coord for coord in candidates if (coord[0] + coord[1]) % 2 == 0
        ]
        if checkerboard:
            return min(checkerboard)
        return min(candidates)

    def on_shot_result(self, coord: Coord, result: ShotResult) -> None:
        self._attempted.add(coord)
        if result == ShotResult.HIT:
            self._active_hits.add(coord)
        elif result == ShotResult.SUNK:
            self._active_hits.clear()

    def _select_local_target(self, board_size: int, candidates: Set[Coord]) -> Coord | None:
        active_hits = {
            coord
            for coord in self._active_hits
            if self._in_bounds(coord, board_size)
        }
        if not active_hits:
            return None

        row_targets = self._line_targets(active_hits, candidates, horizontal=True)
        if row_targets:
            return row_targets[0]

        col_targets = self._line_targets(active_hits, candidates, horizontal=False)
        if col_targets:
            return col_targets[0]

        targets = []
        for row, col in sorted(active_hits):
            targets.extend(
                [
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                ]
            )
        legal_targets = [
            coord for coord in targets if self._in_bounds(coord, board_size) and coord in candidates
        ]
        if legal_targets:
            return legal_targets[0]
        return None

    def _line_targets(
        self, active_hits: Set[Coord], candidates: Set[Coord], *, horizontal: bool
    ) -> list[Coord]:
        groups: dict[int, list[int]] = {}
        for row, col in active_hits:
            key = row if horizontal else col
            value = col if horizontal else row
            groups.setdefault(key, []).append(value)

        targets: list[Coord] = []
        for key in sorted(groups):
            values = sorted(groups[key])
            if len(values) < 2:
                continue
            before = values[0] - 1
            after = values[-1] + 1
            if horizontal:
                possible = [(key, before), (key, after)]
            else:
                possible = [(before, key), (after, key)]
            targets.extend(coord for coord in possible if coord in candidates)
        return targets

    def _in_bounds(self, coord: Coord, board_size: int) -> bool:
        row, col = coord
        return 0 <= row < board_size and 0 <= col < board_size
