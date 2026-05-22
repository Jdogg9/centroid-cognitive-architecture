from core.evaluation.probes import distributed_coordination_probe


def test_distributed_coordination_probe() -> None:
    result = distributed_coordination_probe(
        [
            {
                "node_sync_latency_ms": 42,
                "max_sync_latency_ms": 100,
                "failover_continuity": 1.0,
                "min_failover_continuity": 1.0,
                "state_propagation_accuracy": 1.0,
                "min_state_propagation_accuracy": 1.0,
            }
        ]
    )
    assert result.passed is True
    assert result.score == 1.0
