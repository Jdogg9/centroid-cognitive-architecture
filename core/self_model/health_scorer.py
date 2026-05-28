"""Per-source health scores with trend detection and system-level rollup.

HealthScorer tracks rolling windows of metrics per source, scores each
node 0.0–1.0, computes improvement/degradation trends via simple linear
regression, and exposes a system_health_ratio() aggregate.
"""

from __future__ import annotations

import time  # noqa: TC003 — keep stdlib import
from collections import deque
from dataclasses import dataclass


@dataclass
class NodeHealth:
    """Health snapshot for one telemetry source."""

    node_id: str
    score: float               # 0.0 – 1.0, mean of recent metric values
    trend: float               # positive = improving, negative = degrading
    sample_count: int
    last_updated: float        # time.time()


class HealthScorer:
    """Tracks health scores and trends for multiple telemetry sources."""

    def __init__(
        self,
        *,
        window: int = 20,
        trend_window: int = 5,
    ) -> None:
        self._window = window
        self._trend_window = trend_window
        # source_id → deque of score values
        self._score_history: dict[str, deque[float]] = {}
        # source_id → NodeHealth
        self._health: dict[str, NodeHealth] = {}

    def update(self, source_id: str, metrics: dict[str, float]) -> NodeHealth:
        """Compute current score from metrics, append to rolling window, compute trend.

        Score = mean of all metric values, each clipped to [0.0, 1.0].
        Missing/error keys are treated as 0.0.
        Trend = slope of linear regression over the last N score values.
        """
        values = [max(0.0, min(1.0, v)) for v in metrics.values()]
        if not values:
            score = 0.0
        else:
            score = sum(values) / len(values)

        # Track score history
        if source_id not in self._score_history:
            self._score_history[source_id] = deque(maxlen=self._window)
        self._score_history[source_id].append(score)

        # Compute trend from recent scores
        trend = _compute_trend(list(self._score_history[source_id]), self._trend_window)

        health = NodeHealth(
            node_id=source_id,
            score=round(score, 4),
            trend=round(trend, 4),
            sample_count=len(self._score_history[source_id]),
            last_updated=time.time(),
        )
        self._health[source_id] = health
        return health

    def all_health(self) -> list[NodeHealth]:
        """Current health for all tracked sources."""
        return list(self._health.values())

    def system_health_ratio(self) -> float:
        """Mean score across all known nodes (0.0 if no sources registered)."""
        if not self._health:
            return 0.0
        return sum(h.score for h in self._health.values()) / len(self._health)


# ── Internal ─────────────────────────────────────────────────────────────


def _compute_trend(scores: list[float], n: int) -> float:
    """Simple linear regression slope over the last n scores.

    Returns a normalized trend: positive = improving, negative = degrading.
    Slope is in units of score-per-sample.
    """
    recent = scores[-n:] if len(scores) >= n else scores
    if len(recent) < 2:
        return 0.0

    m = len(recent)
    x_mean = (m - 1) / 2.0
    y_mean = sum(recent) / m

    numerator = sum((i - x_mean) * (recent[i] - y_mean) for i in range(m))
    denominator = sum((i - x_mean) ** 2 for i in range(m))

    if denominator == 0:
        return 0.0

    return numerator / denominator
