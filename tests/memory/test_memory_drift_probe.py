from core.evaluation.probes import memory_drift_probe


def test_memory_drift_probe() -> None:
    result = memory_drift_probe(
        [
            {
                "before_recall": ["goal:continuity", "policy:approval"],
                "after_recall": ["goal:continuity", "policy:approval"],
                "max_drift": 0.0,
            }
        ]
    )
    assert result.passed is True
    assert result.score == 1.0
