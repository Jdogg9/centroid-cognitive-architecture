"""Probe tests for the TF-IDF memory search and pyramid compaction."""

from dataclasses import asdict
from pathlib import Path

from core.memory import (
    Event,
    IndexEntry,
    MemoryPyramid,
    MemoryStore,
    SearchResult,
    TfidfIndex,
    TierCapacity,
    compute_salience,
)
from tests.schema_helpers import validate_schema


# ── TF-IDF index ──────────────────────────────────────────────────────────


def _build_sample_store(path: Path) -> MemoryStore:
    store = MemoryStore(path)
    events = [
        Event("observation", "node liveness check passed", "sensory_stream", metadata={"severity": "low"}),
        Event("decision", "route high-priority signal to reflex path", "event_journal", metadata={"severity": "medium"}),
        Event("safety_event", "safety gate denied destructive file write", "audit_log", metadata={"severity": "critical"}),
        Event("checkpoint", "memory compaction completed successfully", "memory_journal", metadata={"severity": "info"}),
        Event("anomaly", "anomaly detected in reflex latency: 450ms exceeds threshold", "deliberation_log", metadata={"severity": "warning"}),
    ]
    for e in events:
        store.append(e)
    return store


def test_tfidf_index_search_exact() -> None:
    """TF-IDF search finds exact content match."""
    idx = TfidfIndex()
    idx.add("e1", "safety gate denied destructive file write", source="audit_log", metadata={"event_type": "safety_event"})
    idx.add("e2", "node liveness check passed", source="sensory_stream")
    idx.add("e3", "memory compaction completed successfully", source="memory_journal")
    idx.recompute_idf()

    results = idx.search("safety gate denial")
    assert len(results) > 0
    assert results[0][0].doc_id == "e1"
    assert results[0][1] > 0.1  # meaningful score


def test_tfidf_index_no_results() -> None:
    """TF-IDF search returns empty list when nothing matches."""
    idx = TfidfIndex()
    idx.add("e1", "node liveness check")
    idx.recompute_idf()
    results = idx.search("quantum entanglement physics")
    assert results == []


def test_tfidf_index_empty() -> None:
    """Empty index returns empty search results."""
    idx = TfidfIndex()
    assert idx.search("anything") == []


# ── Memory store search ──────────────────────────────────────────────────


def test_memory_store_search_and_schema(tmp_path) -> None:
    """MemoryStore.search() returns relevant results and valid schema."""
    store = _build_sample_store(tmp_path / "events.jsonl")

    results = store.search("safety", top_k=3)
    assert len(results) >= 1
    assert isinstance(results[0], SearchResult)
    assert results[0].source == "audit_log"
    assert results[0].event_type == "safety_event"

    # Validate schema on each result's backing event
    evts = store.tail()
    for evt in evts:
        payload = {
            **asdict(evt),
            "classification": "event_journal",
            "provenance": "unit-test",
            "redacted": False,
        }
        validate_schema("memory_event.schema.json", payload)


def test_memory_store_search_provenance_tracking(tmp_path) -> None:
    """Repeated searches update provenance record."""
    store = _build_sample_store(tmp_path / "events.jsonl")

    # Search twice for same term
    store.search("liveness")
    results = store.search("liveness")
    assert len(results) > 0
    assert results[0].provenance_record is not None
    assert results[0].provenance_record.retrieval_count >= 2


# ── Salience scoring ─────────────────────────────────────────────────────


def test_compute_salience_high_for_decision() -> None:
    """Decision events score higher salience when source weights apply."""
    entry = IndexEntry(
        doc_id="d1",
        text="decision: route high-priority signal to reflex path",
        source="event_journal",
        metadata={"event_type": "decision"},
    )
    score = compute_salience(entry)
    # event_journal source (0.18) + decision type (0.22) + "decision" signal (0.12) + base (0.1) = 0.62
    assert score > 0.40


def test_compute_salience_low_for_plain_observation() -> None:
    """Plain observations score lower salience than decisions."""
    entry = IndexEntry(
        doc_id="d2",
        text="observation: node check completed",
        source="sensory_stream",
        metadata={},
    )
    score = compute_salience(entry)
    # sensory_stream source (0.12) + no event_type + no signals + base (0.1) = 0.22
    assert score < 0.30


# ── Memory pyramid ───────────────────────────────────────────────────────


def test_memory_pyramid_tier_classification(tmp_path) -> None:
    """Tiers are assigned based on salience and age."""
    store = _build_sample_store(tmp_path / "events.jsonl")
    pyramid = MemoryPyramid(capacity=TierCapacity(active=5, working=10, long_term=20))

    decisions = pyramid.classify_all(store._index.entries)
    tiers = {d.tier for d in decisions}
    # All entries should classify into some tier
    assert len(decisions) == store.index_size
    # Expect at least 2 tiers across 5 entries
    assert len(tiers) >= 2


def test_memory_pyramid_compaction_retains_most(tmp_path) -> None:
    """Compaction retains most entries under generous capacity."""
    store = _build_sample_store(tmp_path / "events.jsonl")
    pyramid = MemoryPyramid(capacity=TierCapacity(active=5, working=10, long_term=10))

    retained_ids, evicted_ids = pyramid.compact(store._index.entries)
    # With generous capacity (5+10+10=25), all 5 entries should be retained
    assert len(retained_ids) == store.index_size
    assert len(evicted_ids) == 0


def test_memory_pyramid_compaction_evicts_under_tight_capacity(tmp_path) -> None:
    """Compaction evicts entries when capacity is tight."""
    store = _build_sample_store(tmp_path / "events.jsonl")
    pyramid = MemoryPyramid(capacity=TierCapacity(active=0, working=2, long_term=1))

    retained_ids, evicted_ids = pyramid.compact(store._index.entries)
    # Capacity is 3 total, 5 entries → at least 1 should be evicted
    assert len(retained_ids) + len(evicted_ids) == store.index_size
    assert len(evicted_ids) >= 1


# ── Store compact() delegation ───────────────────────────────────────────


def test_memory_store_compact_delegates(tmp_path) -> None:
    """MemoryStore.compact() returns retained and evicted doc IDs covering all entries."""
    store = _build_sample_store(tmp_path / "events.jsonl")
    retained_ids, evicted_ids = store.compact()
    assert isinstance(retained_ids, list)
    assert isinstance(evicted_ids, list)
    assert len(retained_ids) + len(evicted_ids) == store.index_size


# ── Tier count ───────────────────────────────────────────────────────────


def test_memory_store_tier_counts(tmp_path) -> None:
    """MemoryStore.tier_counts() returns counts per tier."""
    store = _build_sample_store(tmp_path / "events.jsonl")
    counts = store.tier_counts()
    assert "active" in counts
    assert "working" in counts
    assert "long_term" in counts
    assert "archive" in counts
    assert sum(counts.values()) == store.index_size


# ── Backward compatibility ───────────────────────────────────────────────


def test_memory_store_original_api_preserved(tmp_path) -> None:
    """append() and tail() work exactly as before."""
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
