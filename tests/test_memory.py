from core.memory import Event, MemoryStore


def test_memory_tail(tmp_path) -> None:
    store = MemoryStore(tmp_path / "events.jsonl")
    store.append(Event(event_type="check", content="ok", source="test"))
    events = store.tail()
    assert len(events) == 1
    assert events[0].content == "ok"

