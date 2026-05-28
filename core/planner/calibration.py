"""Bayesian calibration tracking for forecast accuracy.

Tracks Mean Absolute Error (MAE) and signed bias per (field, horizon)
pair. Incremental updates with atomic JSON persistence.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class CalibrationRecord:
    """Tracking data for one field+horizon prediction pair."""

    field: str
    horizon: str
    mae: float = 0.0       # mean absolute error
    bias: float = 0.0      # mean signed error (positive = over-predicts)
    sample_count: int = 0


class CalibrationStore:
    """Persistent accuracy tracker for forecast feedback."""

    def __init__(self, state_path: str | Path = "state/calibration.json") -> None:
        self._path = Path(state_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, CalibrationRecord] = {}  # keyed by "field:horizon"
        self.load()

    def update(
        self, field: str, horizon: str, predicted: float, actual: float
    ) -> CalibrationRecord:
        """Update calibration with a new prediction-actual pair.

        Incremental mean:
            MAE' = (MAE × n + |error|) / (n + 1)
            bias' = (bias × n + error) / (n + 1)
        """
        key = f"{field}:{horizon}"
        rec = self._records.get(key)

        if rec is None:
            rec = CalibrationRecord(field=field, horizon=horizon)
            self._records[key] = rec

        error = predicted - actual
        n = rec.sample_count

        rec.mae = round((rec.mae * n + abs(error)) / (n + 1), 6)
        rec.bias = round((rec.bias * n + error) / (n + 1), 6)
        rec.sample_count = n + 1

        self._persist()
        return rec

    def get(self, field: str, horizon: str) -> CalibrationRecord | None:
        """Get calibration record for a field+horizon pair, or None."""
        key = f"{field}:{horizon}"
        return self._records.get(key)

    def all_records(self) -> list[CalibrationRecord]:
        """All tracked calibration records."""
        return list(self._records.values())

    def load(self) -> None:
        """Read calibration data from disk. No-op if file missing."""
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            raw_list = data.get("records", [])
            self._records.clear()
            for entry in raw_list:
                rec = CalibrationRecord(
                    field=entry["field"],
                    horizon=entry["horizon"],
                    mae=float(entry.get("mae", 0.0)),
                    bias=float(entry.get("bias", 0.0)),
                    sample_count=int(entry.get("sample_count", 0)),
                )
                key = f"{rec.field}:{rec.horizon}"
                self._records[key] = rec
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # ── Internal ──────────────────────────────────────────────────────────

    def _persist(self) -> None:
        """Atomic write to state/calibration.json."""
        data = {
            "records": [asdict(r) for r in self._records.values()],
        }
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self._path)
