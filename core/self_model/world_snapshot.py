"""World snapshot — atomic JSON state file writes and reads.

SnapshotWriter writes state/world_snapshot.json and state/world_trends.json
atomically (write .tmp, then os.replace). These files become the live value
source for the Module Coherence Graph in Phase 2.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class WorldSnapshot:
    """Serialized self-model state for cross-module consumption."""

    timestamp: float
    node_health: dict[str, float]       # source_id → score
    node_trends: dict[str, float]       # source_id → trend
    system_health_ratio: float
    anomaly_count: int
    coherence_index: float | None = None  # Phase 2 wires this in


class SnapshotWriter:
    """Atomic JSON snapshot persistence."""

    def __init__(self, state_dir: str | Path = "state") -> None:
        self._dir = Path(state_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._snapshot_path = self._dir / "world_snapshot.json"
        self._trends_path = self._dir / "world_trends.json"

    def write(self, snapshot: WorldSnapshot) -> None:
        """Write snapshot and trends atomically."""
        data = asdict(snapshot)
        self._atomic_write(self._snapshot_path, data)
        # Trends subset for separate file
        trends_data: dict[str, Any] = {
            "timestamp": snapshot.timestamp,
            "node_trends": snapshot.node_trends,
            "system_health_ratio": snapshot.system_health_ratio,
        }
        self._atomic_write(self._trends_path, trends_data)

    def read_snapshot(self) -> WorldSnapshot | None:
        """Read world_snapshot.json, return None if missing or corrupt."""
        if not self._snapshot_path.exists():
            return None
        try:
            data = json.loads(self._snapshot_path.read_text(encoding="utf-8"))
            return WorldSnapshot(**data)
        except (json.JSONDecodeError, TypeError):
            return None

    @staticmethod
    def _atomic_write(path: Path, data: dict[str, Any]) -> None:
        """Write to .tmp, then atomically replace target."""
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
