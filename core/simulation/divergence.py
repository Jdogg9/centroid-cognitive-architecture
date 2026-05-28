"""Recency-weighted divergence metric D(t) for twin-vs-actual comparison.

D(t) = Σ λ^(n−k) × d_k where d_k is the point divergence at sample k,
λ is the temporal decay factor, and n is total sample count.

A positive divergence_trend means the twin is drifting away from actual
— the simulation is worsening. Negative means converging.
"""

from __future__ import annotations

import statistics
from collections import deque
from dataclasses import dataclass, field


@dataclass
class DivergenceSample:
    """A single comparison between actual and twin state."""

    cycle: int
    actual_values: dict[str, float]
    twin_values: dict[str, float]
    point_divergence: float  # mean absolute difference across shared float fields


@dataclass
class DivergenceMetric:
    """Aggregated divergence over a full simulation run."""

    fork_id: str
    samples: list[DivergenceSample]
    weighted_divergence: float       # D(t) = Σ λ^(n−k) × d_k
    lambda_: float                   # decay factor used
    divergence_trend: float          # slope over point_divergence values


class DivergenceCalculator:
    """Track twin-vs-actual divergence across simulation cycles."""

    def __init__(self, lambda_: float = 0.9, max_samples: int = 20) -> None:
        self._lambda = lambda_
        self._max_samples = max_samples
        self._samples: dict[str, deque[DivergenceSample]] = {}

    def sample(
        self,
        fork_id: str,
        actual: dict,
        twin: dict,
        cycle: int,
    ) -> DivergenceSample:
        """Record one comparison between actual and twin state.

        point_divergence = mean(|actual[k] − twin[k]|) over shared float keys.
        """
        # Extract shared keys with float values from both dicts
        actual_floats: dict[str, float] = {}
        for k, v in actual.items():
            if isinstance(v, (int, float)):
                actual_floats[k] = float(v)
        twin_floats: dict[str, float] = {}
        for k, v in twin.items():
            if isinstance(v, (int, float)):
                twin_floats[k] = float(v)

        shared = set(actual_floats) & set(twin_floats)
        if not shared:
            point_div = 0.0
        else:
            point_div = sum(
                abs(actual_floats[k] - twin_floats[k]) for k in shared
            ) / len(shared)

        s = DivergenceSample(
            cycle=cycle,
            actual_values=actual_floats,
            twin_values=twin_floats,
            point_divergence=round(point_div, 6),
        )

        if fork_id not in self._samples:
            self._samples[fork_id] = deque(maxlen=self._max_samples)
        self._samples[fork_id].append(s)

        return s

    def compute(self, fork_id: str) -> DivergenceMetric:
        """Compute D(t) with recency-weighted compounding.

        D(t) = Σ λ^(n−k) × d_k  where n = total samples,
        k = 1-based index (oldest first), most recent has highest weight.
        """
        samples_q = self._samples.get(fork_id)
        if not samples_q:
            return DivergenceMetric(
                fork_id=fork_id,
                samples=[],
                weighted_divergence=0.0,
                lambda_=self._lambda,
                divergence_trend=0.0,
            )

        samples = list(samples_q)
        n = len(samples)

        # Weighted divergence: most recent sample (k=n) gets weight λ^0 = 1
        weighted = 0.0
        weight_sum = 0.0
        for k, s in enumerate(samples, start=1):
            weight = self._lambda ** (n - k)
            weighted += weight * s.point_divergence
            weight_sum += weight

        d_t = weighted / weight_sum if weight_sum > 0 else 0.0

        # Trend: linear regression slope over point_divergence
        if len(samples) < 2:
            trend = 0.0
        else:
            point_divs = [s.point_divergence for s in samples]
            trend = _compute_slope(point_divs)

        return DivergenceMetric(
            fork_id=fork_id,
            samples=list(samples),
            weighted_divergence=round(d_t, 6),
            lambda_=self._lambda,
            divergence_trend=round(trend, 6),
        )

    def clear(self, fork_id: str) -> None:
        """Remove all samples for a fork after preflight resolves."""
        self._samples.pop(fork_id, None)


def _compute_slope(values: list[float]) -> float:
    """Simple linear regression slope."""
    n = len(values)
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    return numerator / denominator if denominator != 0 else 0.0
