from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .metrics import MetricResult, clamp_score
from .probes import (
    action_correction_probe,
    continuity_probe,
    distributed_coordination_probe,
    memory_probe,
    memory_drift_probe,
    priority_probe,
    reconciliation_probe,
    routing_probe,
    safety_probe,
    self_model_probe,
    temporal_probe,
)

PROBES = {
    "action_correction": action_correction_probe,
    "continuity": continuity_probe,
    "distributed_coordination": distributed_coordination_probe,
    "memory": memory_probe,
    "memory_drift": memory_drift_probe,
    "priority": priority_probe,
    "reconciliation": reconciliation_probe,
    "routing": routing_probe,
    "safety": safety_probe,
    "self_model": self_model_probe,
    "temporal": temporal_probe,
}


@dataclass(frozen=True)
class EvaluationReport:
    suite_name: str
    score: float
    passed: bool
    results: list[MetricResult]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["results"] = [result.to_dict() for result in self.results]
        return data


class EvaluationHarness:
    def __init__(self, minimum_score: float = 0.85):
        self.minimum_score = minimum_score

    def run_file(self, fixture_path: Path) -> EvaluationReport:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        return self.run_fixture(fixture)

    def run_fixture(self, fixture: dict) -> EvaluationReport:
        results: list[MetricResult] = []
        for probe_name, cases in fixture.get("probes", {}).items():
            if probe_name not in PROBES:
                raise ValueError(f"unknown evaluation probe: {probe_name}")
            results.append(PROBES[probe_name](cases))

        score = self._weighted_score(results)
        return EvaluationReport(
            suite_name=fixture.get("suite_name", "unnamed"),
            score=score,
            passed=score >= self.minimum_score and all(result.passed for result in results),
            results=results,
        )

    @staticmethod
    def _weighted_score(results: list[MetricResult]) -> float:
        if not results:
            return 0.0
        return clamp_score(sum(result.score for result in results) / len(results))
