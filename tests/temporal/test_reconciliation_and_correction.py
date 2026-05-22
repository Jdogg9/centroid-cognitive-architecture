from core.evaluation.probes import action_correction_probe, reconciliation_probe


def test_reconciliation_and_action_correction_probes() -> None:
    reconciliation = reconciliation_probe(
        [
            {
                "reflex_response_ms": 31,
                "deliberative_response_ms": 4200,
                "state_reconciliation_ms": 4388,
                "max_reflex_ms": 100,
                "max_deliberative_ms": 5000,
                "max_reconciliation_ms": 6000,
            }
        ]
    )
    correction = action_correction_probe(
        [{"correction_ms": 740, "max_correction_ms": 1000, "correction_applied": True}]
    )
    assert reconciliation.passed is True
    assert correction.passed is True
