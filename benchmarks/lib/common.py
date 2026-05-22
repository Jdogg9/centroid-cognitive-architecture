from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class BenchmarkResult:
    benchmark: str
    metrics: dict[str, float]
    passed: bool

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def print_result(result: BenchmarkResult) -> None:
    print(result.to_json())
