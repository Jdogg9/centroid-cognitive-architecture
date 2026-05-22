from __future__ import annotations

import json
from pathlib import Path

from tests.schema_helpers import validate_schema


def test_memory_example_is_valid() -> None:
    payload = json.loads(
        Path("schemas/examples/memory_event.example.json").read_text(encoding="utf-8")
    )
    validate_schema("memory_event.schema.json", payload)
    assert payload["classification"] == "privileged"
