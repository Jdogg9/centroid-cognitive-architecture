from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.run_distributed_benchmark import run as run_distributed
from benchmarks.run_latency_benchmark import run as run_latency
from benchmarks.run_memory_benchmark import run as run_memory
from benchmarks.run_throughput_benchmark import run as run_throughput


def main() -> int:
    results = [run_latency(), run_memory(), run_distributed(), run_throughput()]
    payload = {
        "passed": all(result.passed for result in results),
        "results": [result.__dict__ for result in results],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
