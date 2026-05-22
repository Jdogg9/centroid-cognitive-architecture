from dataclasses import asdict

from core.memory import Event, MemoryStore
from tests.schema_helpers import validate_schema


def test_memory_store_roundtrip_and_schema(tmp_path) -> None:
    store = MemoryStore(tmp_path / "events.jsonl")
    event = Event(
        event_type="protected_checkpoint",
        content="public continuity checkpoint",
        source="test",
        metadata={"classification": "privileged"},
    )
    store.append(event)

    latest = store.tail(limit=1)[0]
    assert latest.content == "public continuity checkpoint"

    payload = {
        **asdict(latest),
        "classification": latest.metadata["classification"],
        "provenance": "unit-test",
        "redacted": False,
    }
    validate_schema("memory_event.schema.json", payload)
