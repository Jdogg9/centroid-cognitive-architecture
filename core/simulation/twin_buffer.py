"""Twin state forking — deep-copy world_snapshot.json for counterfactual
simulation. The twin is fully isolated from actual runtime state.
"""

from __future__ import annotations

import copy
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TwinState:
    """An isolated snapshot fork for counterfactual simulation."""

    snapshot: dict           # deep copy of world_snapshot contents
    forked_at: float         # time.time()
    fork_id: str             # uuid4 hex — links twin to its origin cycle
    cycle: int               # cycle counter at fork time


class TwinBuffer:
    """Isolated state forking — no mutations leak to the real world."""

    def __init__(self, snapshot_path: str | Path = "state/world_snapshot.json") -> None:
        self._path = Path(snapshot_path)
        self._cycle: int = 0

    @property
    def cycle(self) -> int:
        return self._cycle

    def tick(self) -> None:
        """Advance the cycle counter (called by preflight)."""
        self._cycle += 1

    def fork(self) -> TwinState:
        """Deep-copy the current world_snapshot.json into an isolated twin.

        Raises FileNotFoundError if the snapshot file is missing.
        """
        if not self._path.exists():
            raise FileNotFoundError(
                f"World snapshot not found at {self._path}. "
                "Run SelfModel.tick() first to produce a snapshot."
            )

        raw = json.loads(self._path.read_text(encoding="utf-8"))
        snapshot = copy.deepcopy(raw)

        return TwinState(
            snapshot=snapshot,
            forked_at=time.time(),
            fork_id=uuid.uuid4().hex,
            cycle=self._cycle,
        )

    def actual_snapshot(self) -> dict:
        """Read the current world_snapshot.json fresh — never cached."""
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))
