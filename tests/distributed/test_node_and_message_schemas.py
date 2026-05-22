from tests.schema_helpers import validate_schema


def test_node_heartbeat_schema() -> None:
    validate_schema(
        "node_heartbeat.schema.json",
        {
            "node_id": "reflex-1",
            "timestamp": "2026-01-01T00:00:00Z",
            "node_role": "reflex_node",
            "status": "healthy",
            "sequence": 1,
            "latency_ms": 12.5,
            "capabilities": ["liveness", "policy_check"],
        },
    )


def test_message_event_schema() -> None:
    validate_schema(
        "message_event.schema.json",
        {
            "message_id": "message-1",
            "timestamp": "2026-01-01T00:00:00Z",
            "source_node": "sensory_node",
            "target_node": "router",
            "intent": "route_observation",
            "priority": 0.75,
            "state_refs": ["state:demo"],
            "requires_approval": False,
            "audit_reason": "demo routing event",
            "payload": {"observation": "node liveness check"},
        },
    )

