from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrioritySignal:
    urgency: float = 0.0
    risk: float = 0.0
    user_value: float = 0.0
    stability: float = 1.0


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_priority(signal: PrioritySignal) -> float:
    """Combine urgency, risk, user value, and stability into one route score."""

    score = (
        0.30 * _clamp(signal.urgency)
        + 0.30 * _clamp(signal.risk)
        + 0.25 * _clamp(signal.user_value)
        + 0.15 * (1.0 - _clamp(signal.stability))
    )
    return round(_clamp(score), 4)
