from __future__ import annotations

import argparse
import json
from pathlib import Path

from .harness import EvaluationHarness


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Centroid evaluation fixtures.")
    parser.add_argument(
        "fixture",
        type=Path,
        nargs="?",
        default=Path("evaluation/fixtures/baseline.json"),
        help="Path to an evaluation fixture JSON file. Defaults to packaged baseline fixture.",
    )
    parser.add_argument("--minimum-score", type=float, default=0.85)
    parser.add_argument("--json", action="store_true", help="Print full JSON report.")
    args = parser.parse_args()

    report = EvaluationHarness(minimum_score=args.minimum_score).run_file(args.fixture)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        status = "PASS" if report.passed else "FAIL"
        print(f"{status} {report.suite_name} score={report.score:.4f}")
        for result in report.results:
            result_status = "PASS" if result.passed else "FAIL"
            print(f"{result_status} {result.name} score={result.score:.4f} {result.details}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
