"""Z-score anomaly detection over rolling per-field metric windows.

Each (source_id, field) pair gets its own independent window. Cold start
protection: no anomalies fire before min_samples is reached. Caller is
responsible for wiring anomalies into MemoryStore — the detector itself
has no store dependency.
"""

from __future__ import annotations

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class AnomalyEvent:
    """A detected anomaly on a single metric field."""

    source_id: str
    field: str
    observed: float
    mean: float
    std: float
    z_score: float
    severity: Literal["warn", "critical"]
    timestamp: float = field(default_factory=time.time)


class AnomalyDetector:
    """Z-score anomaly detection over per-field rolling windows."""

    def __init__(
        self,
        *,
        warn_threshold: float = 2.0,
        critical_threshold: float = 3.5,
        min_samples: int = 5,
        window: int = 20,
    ) -> None:
        self._warn_threshold = warn_threshold
        self._critical_threshold = critical_threshold
        self._min_samples = min_samples
        self._window = window
        # (source_id, field) → deque of float values
        self._windows: dict[tuple[str, str], deque[float]] = {}

    def update(self, source_id: str, metrics: dict[str, float]) -> list[AnomalyEvent]:
        """Feed new metrics in, return any anomalies detected.

        Uses the values *before* adding the current one to compute
        baseline mean/std, so the spike itself doesn't dilute its own
        z-score. Returns [] when no anomalies (never returns None).
        """
        anomalies: list[AnomalyEvent] = []

        for field, value in metrics.items():
            key = (source_id, field)
            if key not in self._windows:
                self._windows[key] = deque(maxlen=self._window)
            self._windows[key].append(value)

            window_values = list(self._windows[key])

            # Cold start: don't fire on insufficient data
            if len(window_values) < self._min_samples:
                continue

            # Compute baseline from prior values (exclude current spike)
            prior = window_values[:-1]
            if len(prior) < 2:
                continue

            mean_val = statistics.mean(prior)
            std_val = statistics.stdev(prior)

            if std_val == 0.0:
                continue

            z = (value - mean_val) / std_val
            abs_z = abs(z)

            severity: Literal["warn", "critical"] | None = None
            if abs_z > self._critical_threshold:
                severity = "critical"
            elif abs_z > self._warn_threshold:
                severity = "warn"

            if severity is not None:
                anomalies.append(
                    AnomalyEvent(
                        source_id=source_id,
                        field=field,
                        observed=round(value, 4),
                        mean=round(mean_val, 4),
                        std=round(std_val, 4),
                        z_score=round(z, 4),
                        severity=severity,
                    )
                )

        return anomalies
