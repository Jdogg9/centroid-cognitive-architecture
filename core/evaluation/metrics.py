from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MetricThreshold:
    name: str
    minimum: float
    weight: float = 1.0


@dataclass(frozen=True)
class MetricResult:
    name: str
    score: float
    passed: bool
    details: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def pass_at(name: str, score: float, minimum: float, details: str = "") -> MetricResult:
    normalized = clamp_score(score)
    return MetricResult(name=name, score=normalized, passed=normalized >= minimum, details=details)
