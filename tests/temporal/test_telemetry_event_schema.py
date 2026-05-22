from datetime import datetime, timedelta

from core.temporal import latency_ms
from tests.schema_helpers import validate_schema


def test_latency_metric_and_telemetry_schema() -> None:
    start = datetime.fromisoformat("2026-01-01T00:00:00+00:00")
    end = start + timedelta(milliseconds=31)
    observed = latency_ms(start, end)

    assert observed == 31.0
    validate_schema(
        "telemetry_event.schema.json",
        {
            "event_id": "telemetry-1",
            "timestamp": "2026-01-01T00:00:00Z",
            "node_id": "reflex-1",
            "metric_name": "reflex_latency_ms",
            "value": observed,
            "unit": "ms",
            "labels": {"loop": "reflex"},
        },
    )

