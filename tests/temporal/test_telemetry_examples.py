from __future__ import annotations

import json
from pathlib import Path

from tests.schema_helpers import validate_schema


def test_telemetry_example_is_valid() -> None:
    payload = json.loads(
        Path("schemas/examples/telemetry_event.example.json").read_text(encoding="utf-8")
    )
    validate_schema("telemetry_event.schema.json", payload)
    assert payload["metric_name"] == "reflex_latency_ms"
    assert payload["value"] <= 100
