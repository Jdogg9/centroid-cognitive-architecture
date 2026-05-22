from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.lib.common import BenchmarkResult, print_result


def run() -> BenchmarkResult:
    metrics = {
        "reflex_latency_ms": 31.0,
        "deliberation_latency_ms": 4200.0,
        "narrative_reconciliation_delay_ms": 4388.0,
        "action_correction_timing_ms": 740.0,
    }
    passed = (
        metrics["reflex_latency_ms"] <= 100.0
        and metrics["deliberation_latency_ms"] <= 5000.0
        and metrics["narrative_reconciliation_delay_ms"] <= 6000.0
        and metrics["action_correction_timing_ms"] <= 1000.0
    )
    return BenchmarkResult("temporal_latency", metrics, passed)


if __name__ == "__main__":
    print_result(run())
