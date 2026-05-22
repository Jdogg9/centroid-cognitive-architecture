from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.lib.common import BenchmarkResult, print_result
from core.router import Router


def run() -> BenchmarkResult:
    router = Router()
    messages = 1000
    decisions = [
        router.route(priority=(index % 100) / 100.0, mutates_state=False)
        for index in range(messages)
    ]
    reflex_count = sum(1 for decision in decisions if decision.node == "reflex_node")
    deliberation_count = sum(1 for decision in decisions if decision.node == "deliberation_node")
    metrics = {
        "messages_processed": float(messages),
        "reflex_routes": float(reflex_count),
        "deliberation_routes": float(deliberation_count),
        "route_consistency": 1.0 if reflex_count + deliberation_count == messages else 0.0,
    }
    return BenchmarkResult("message_throughput", metrics, metrics["route_consistency"] == 1.0)


if __name__ == "__main__":
    print_result(run())
