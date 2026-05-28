from __future__ import annotations

import argparse
import json
from pathlib import Path

from .harness import EvaluationHarness, EvaluationReport

SUITE_FIXTURES: dict[str, Path] = {
    "baseline": Path("evaluation/fixtures/baseline.json"),
    "memory": Path("evaluation/fixtures/memory.json"),
    "self_model": Path("evaluation/fixtures/self_model.json"),
    "coherence": Path("evaluation/fixtures/coherence.json"),
    "planner": Path("evaluation/fixtures/planner.json"),
    "simulation": Path("evaluation/fixtures/simulation.json"),
    "sensory": Path("evaluation/fixtures/sensory.json"),
    "fusion": Path("evaluation/fixtures/fusion.json"),
}

SUITE_ORDER = tuple(SUITE_FIXTURES)


def resolve_suite_fixtures(suite: str, fixture: Path | None = None) -> list[tuple[str, Path]]:
    """Resolve a named evaluation suite to one or more fixture files.

    Passing an explicit fixture preserves the original single-fixture CLI path.
    """
    if fixture is not None:
        return [(fixture.stem, fixture)]
    if suite == "all":
        return [(name, SUITE_FIXTURES[name]) for name in SUITE_ORDER]
    if suite not in SUITE_FIXTURES:
        valid = ", ".join((*SUITE_ORDER, "all"))
        raise ValueError(f"unknown suite '{suite}' (valid: {valid})")
    return [(suite, SUITE_FIXTURES[suite])]


def _probe_count(report: EvaluationReport) -> int:
    return len(report.results)


def _print_suite_summary(name: str, report: EvaluationReport) -> None:
    print(
        f"suite={name:<16} passed={str(report.passed).lower():<5} "
        f"score={report.score:.4f}  probes={_probe_count(report)}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Centroid evaluation fixtures.")
    parser.add_argument(
        "fixture",
        type=Path,
        nargs="?",
        default=None,
        help="Path to an evaluation fixture JSON file. Defaults to the selected suite fixture.",
    )
    parser.add_argument(
        "--mode",
        choices=("full",),
        default="full",
        help="Evaluation mode. Currently only 'full' is implemented.",
    )
    parser.add_argument(
        "--suite",
        choices=(*SUITE_ORDER, "all"),
        default="baseline",
        help="Named fixture suite to run. Defaults to baseline, preserving original behavior.",
    )
    parser.add_argument("--minimum-score", type=float, default=0.85)
    parser.add_argument("--json", action="store_true", help="Print full JSON report.")
    args = parser.parse_args()

    harness = EvaluationHarness(minimum_score=args.minimum_score)
    fixture_specs = resolve_suite_fixtures(args.suite, args.fixture)
    reports = [(name, harness.run_file(path)) for name, path in fixture_specs]

    if args.json:
        payload = {
            "mode": args.mode,
            "suite": args.suite if args.fixture is None else str(args.fixture),
            "reports": [report.to_dict() for _, report in reports],
            "total": {
                "passed": all(report.passed for _, report in reports),
                "score": round(
                    sum(report.score * _probe_count(report) for _, report in reports)
                    / max(1, sum(_probe_count(report) for _, report in reports)),
                    4,
                ),
                "probes": sum(_probe_count(report) for _, report in reports),
            },
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if len(reports) == 1:
            name, report = reports[0]
            _print_suite_summary(name, report)
            for result in report.results:
                result_status = "PASS" if result.passed else "FAIL"
                print(f"{result_status} {result.name} score={result.score:.4f} {result.details}")
        else:
            for name, report in reports:
                _print_suite_summary(name, report)
            total_probes = sum(_probe_count(report) for _, report in reports)
            total_passed = all(report.passed for _, report in reports)
            total_score = round(
                sum(report.score * _probe_count(report) for _, report in reports)
                / max(1, total_probes),
                4,
            )
            print("---")
            print(
                f"total{'':<19} passed={str(total_passed).lower():<5} "
                f"score={total_score:.4f}  probes={total_probes}"
            )

    return 0 if all(report.passed for _, report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
