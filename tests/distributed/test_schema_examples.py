from __future__ import annotations

import json
from pathlib import Path

from tests.schema_helpers import validate_schema

EXAMPLES = {
    "message_event.example.json": "message_event.schema.json",
    "node_heartbeat.example.json": "node_heartbeat.schema.json",
    "evaluation_result.example.json": "evaluation_result.schema.json",
}


def test_distributed_schema_examples_are_valid() -> None:
    example_dir = Path("schemas/examples")
    for example_name, schema_name in EXAMPLES.items():
        payload = json.loads((example_dir / example_name).read_text(encoding="utf-8"))
        validate_schema(schema_name, payload)
