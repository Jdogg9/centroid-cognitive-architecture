from pathlib import Path

from core.evaluation import EvaluationHarness
from tests.schema_helpers import validate_schema


def test_baseline_fixture_passes() -> None:
    report = EvaluationHarness().run_file(Path("evaluation/fixtures/baseline.json"))
    assert report.passed is True
    assert report.score == 1.0
    assert len(report.results) == 29


def test_unknown_probe_rejected() -> None:
    harness = EvaluationHarness()
    try:
        harness.run_fixture({"suite_name": "bad", "probes": {"unknown": []}})
    except ValueError as exc:
        assert "unknown evaluation probe" in str(exc)
    else:
        raise AssertionError("unknown probe should raise ValueError")


def test_evaluation_report_schema() -> None:
    report = EvaluationHarness().run_file(Path("evaluation/fixtures/baseline.json"))
    validate_schema("evaluation_result.schema.json", report.to_dict())
