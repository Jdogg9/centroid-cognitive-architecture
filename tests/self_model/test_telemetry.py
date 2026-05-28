"""Probe tests for self_model telemetry, health scoring, anomaly detection,
and world snapshot persistence.

All probes must pass at score=1.0 in the evaluation harness.
"""

from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import asdict
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.memory import Event, MemoryStore
from core.self_model import (
    AnomalyDetector,
    HealthScorer,
    SelfModel,
    SelfModelSnapshot,
    SnapshotWriter,
    TelemetryAggregator,
    TelemetrySource,
    WorldSnapshot,
)
from tests.schema_helpers import validate_schema


# ── Helpers ────────────────────────────────────────────────────────────────


class _FakeSource:
    """A TelemetrySource duck-type for testing."""

    def __init__(self, source_id: str, metrics: dict[str, float] | None = None) -> None:
        self.source_id = source_id
        self._metrics = metrics or {}

    def read(self) -> dict[str, float]:
        return dict(self._metrics)

    def set_metrics(self, metrics: dict[str, float]) -> None:
        self._metrics = metrics


class _FaultySource:
    """A TelemetrySource that always raises."""

    def __init__(self, source_id: str = "faulty") -> None:
        self.source_id = source_id
        self.read_call_count = 0

    def read(self) -> dict[str, float]:
        self.read_call_count += 1
        raise RuntimeError("simulated failure")


# ── Telemetry Aggregator ───────────────────────────────────────────────────


def test_telemetry_aggregator_collect() -> None:
    """collect() returns dict keyed by source_id."""
    agg = TelemetryAggregator()
    agg.register(_FakeSource("cpu", {"usage_pct": 42.0, "temp_c": 55.0}))
    agg.register(_FakeSource("memory", {"used_gb": 8.0, "total_gb": 16.0}))

    result = agg.collect()
    assert "cpu" in result
    assert "memory" in result
    assert result["cpu"]["usage_pct"] == 42.0
    assert result["memory"]["used_gb"] == 8.0


def test_telemetry_aggregator_fault_tolerance() -> None:
    """A faulty source doesn't crash the aggregator; healthy sources still return."""
    agg = TelemetryAggregator()
    agg.register(_FakeSource("healthy", {"ok": 1.0}))
    faulty = _FaultySource()
    agg.register(faulty)

    result = agg.collect()
    assert "healthy" in result
    assert result["healthy"]["ok"] == 1.0
    # Faulty source gets error sentinel, not a crash
    assert "faulty" in result
    assert result["faulty"]["error"] == 1.0
    assert faulty.read_call_count == 1  # it was called


def test_telemetry_aggregator_no_sources() -> None:
    """Empty aggregator returns empty dict."""
    agg = TelemetryAggregator()
    assert agg.collect() == {}


# ── Health Scorer ──────────────────────────────────────────────────────────


def test_health_scorer_score_bounds() -> None:
    """Score is always in [0.0, 1.0]."""
    hs = HealthScorer()
    h = hs.update("test", {"a": 0.5, "b": 0.8})
    assert 0.0 <= h.score <= 1.0
    assert h.sample_count == 1


def test_health_scorer_clips_out_of_range() -> None:
    """Values outside [0,1] are clipped."""
    hs = HealthScorer()
    h = hs.update("test", {"a": -5.0, "b": 10.0})
    # mean of (-5 clipped to 0) and (10 clipped to 1) = 0.5
    assert h.score == 0.5


def test_health_scorer_trend_direction() -> None:
    """Trend is positive when metrics improve over time."""
    hs = HealthScorer(trend_window=5)
    # Decreasing (improving) sequence
    for v in [0.2, 0.3, 0.5, 0.7, 0.9]:
        hs.update("test", {"metric": v})
    h = hs.update("test", {"metric": 1.0})
    assert h.trend > 0.0


def test_health_scorer_trend_negative() -> None:
    """Trend is negative when metrics degrade."""
    hs = HealthScorer(trend_window=5)
    for v in [1.0, 0.9, 0.7, 0.5, 0.3]:
        hs.update("test", {"metric": v})
    h = hs.update("test", {"metric": 0.1})
    assert h.trend < 0.0


def test_health_scorer_system_ratio() -> None:
    """system_health_ratio matches mean of all node scores."""
    hs = HealthScorer()
    hs.update("n1", {"a": 1.0})
    hs.update("n2", {"a": 0.0})
    hs.update("n3", {"a": 0.5})
    ratio = hs.system_health_ratio()
    assert ratio == pytest.approx(0.5, abs=0.01)


def test_health_scorer_system_ratio_empty() -> None:
    """system_health_ratio returns 0.0 with no sources."""
    hs = HealthScorer()
    assert hs.system_health_ratio() == 0.0


def test_health_scorer_all_health() -> None:
    """all_health() returns list of NodeHealth for all tracked sources."""
    hs = HealthScorer()
    hs.update("n1", {"a": 0.5})
    hs.update("n2", {"a": 0.8})
    healths = hs.all_health()
    assert len(healths) == 2
    assert {h.node_id for h in healths} == {"n1", "n2"}


# ── Anomaly Detector ──────────────────────────────────────────────────────


def test_anomaly_detector_cold_start() -> None:
    """No anomalies fired before min_samples reached."""
    ad = AnomalyDetector(min_samples=5)
    for i in range(4):
        result = ad.update("src", {"f": float(i)})
        assert result == []


def test_anomaly_detector_z_score_warn() -> None:
    """Fires warn at |z| > 2.0."""
    ad = AnomalyDetector(warn_threshold=2.0, critical_threshold=10.0, min_samples=5)
    base = [50.0] * 9  # mean=50, std~0 — then spike
    for v in base:
        result = ad.update("src", {"cpu": v})
        assert result == []
    # Inject a spike: 50→80 is a large z if std is small after 9 base samples
    # Actually std will be ~0 with identical values. Need variance.
    # Reset and use varied base
    ad2 = AnomalyDetector(warn_threshold=2.0, critical_threshold=10.0, min_samples=5)
    base_seq = [50.0, 51.0, 49.0, 52.0, 48.0]  # mean=50, std≈1.58
    for v in base_seq:
        result = ad2.update("src", {"cpu": v})
        assert result == []
    # spike at 55: z ≈ (55-50)/1.58 ≈ 3.16 → > 2.0 warn
    result = ad2.update("src", {"cpu": 55.0})
    assert len(result) == 1
    assert result[0].severity == "warn"


def test_anomaly_detector_z_score_critical() -> None:
    """Fires critical at |z| > 3.5."""
    ad = AnomalyDetector(warn_threshold=2.0, critical_threshold=3.5, min_samples=5)
    base_seq = [50.0, 51.0, 49.0, 52.0, 48.0]  # mean=50, std≈1.58
    for v in base_seq:
        result = ad.update("src", {"cpu": v})
        assert result == []
    # spike at 57: z ≈ (57-50)/1.58 ≈ 4.43 → > 3.5 critical
    result = ad.update("src", {"cpu": 57.0})
    assert len(result) == 1
    assert result[0].severity == "critical"


def test_anomaly_detector_no_false_positives() -> None:
    """A stable metric sequence yields no anomalies."""
    ad = AnomalyDetector(min_samples=5)
    for i in range(20):
        result = ad.update("src", {"stable": 50.0 + (i % 3 - 1) * 0.2})  # tiny jitter
    assert result == []


# ── World Snapshot ────────────────────────────────────────────────────────


def test_world_snapshot_write_read_roundtrip(tmp_path) -> None:
    """write() then read_snapshot() returns matching data."""
    sw = SnapshotWriter(state_dir=str(tmp_path))
    snap = WorldSnapshot(
        timestamp=1234567890.0,
        node_health={"memory": 0.9, "router": 0.75},
        node_trends={"memory": 0.01, "router": -0.02},
        system_health_ratio=0.825,
        anomaly_count=0,
        coherence_index=None,
    )
    sw.write(snap)
    result = sw.read_snapshot()
    assert result is not None
    assert result.timestamp == snap.timestamp
    assert result.node_health == snap.node_health
    assert result.node_trends == snap.node_trends
    assert result.system_health_ratio == snap.system_health_ratio
    assert result.anomaly_count == snap.anomaly_count
    assert result.coherence_index is None


def test_world_snapshot_atomic_write(tmp_path) -> None:
    """.tmp file is not left behind on successful write."""
    state_dir = tmp_path / "state"
    sw = SnapshotWriter(state_dir=str(state_dir))
    snap = WorldSnapshot(
        timestamp=time.time(),
        node_health={},
        node_trends={},
        system_health_ratio=0.0,
        anomaly_count=0,
    )
    sw.write(snap)
    # No .tmp files should remain
    tmp_files = list(state_dir.glob("*.tmp"))
    assert len(tmp_files) == 0
    # But the actual files exist
    assert (state_dir / "world_snapshot.json").exists()
    assert (state_dir / "world_trends.json").exists()


def test_world_snapshot_read_missing() -> None:
    """read_snapshot() returns None when file doesn't exist."""
    sw = SnapshotWriter(state_dir="/tmp/nonexistent_centroid_dir_x2z")
    assert sw.read_snapshot() is None


# ── SelfModel Backward Compatibility ──────────────────────────────────────


def test_self_model_backward_compat_health_ratio() -> None:
    """health_ratio and status work with zero sources registered."""
    sm = SelfModel()
    assert sm.health_ratio == 0.0
    assert sm.status == "critical"


def test_self_model_snapshot_preserved() -> None:
    """Original SelfModelSnapshot is unmodified."""
    s = SelfModelSnapshot(nodes_alive=3, nodes_total=3, active_goals=["test"])
    assert s.status == "healthy"
    assert s.health_ratio == 1.0
    assert s.active_goals == ["test"]


# ── SelfModel Pipeline ────────────────────────────────────────────────────


def test_self_model_tick_emits_snapshot(tmp_path) -> None:
    """tick() returns a WorldSnapshot with valid fields."""
    sm = SelfModel(state_dir=str(tmp_path))
    src = _FakeSource("memory", {"latency_ms": 12.0, "hit_rate": 0.95})
    sm.register_source(src)

    snap = sm.tick()
    assert isinstance(snap, WorldSnapshot)
    assert "memory" in snap.node_health
    assert "memory" in snap.node_trends
    assert 0.0 <= snap.system_health_ratio <= 1.0
    assert snap.coherence_index is None  # not yet wired


def test_self_model_anomaly_appended(tmp_path) -> None:
    """anomaly event lands in MemoryStore when store is provided."""
    store_path = tmp_path / "events.jsonl"
    ms = MemoryStore(store_path)
    sm = SelfModel(memory_store=ms, state_dir=str(tmp_path), warn_threshold=2.0, critical_threshold=10.0)

    src = _FakeSource("router", {"latency_ms": 5.0})
    sm.register_source(src)

    # Build baseline with stable metrics
    for i in range(10):
        src.set_metrics({"latency_ms": 5.0 + (i % 3 - 1) * 0.1})
        sm.tick()

    # Inject anomaly: large spike
    src.set_metrics({"latency_ms": 50.0})
    sm.tick()

    # Search memory for anomaly events
    results = ms.search("anomaly", top_k=5)
    anomaly_events = [r for r in results if r.event_type == "anomaly"]
    assert len(anomaly_events) >= 1

    # Validate schema on the stored anomaly event
    evts = ms.tail(limit=50)
    anomaly_evts = [e for e in evts if e.event_type == "anomaly"]
    assert len(anomaly_evts) >= 1

    ae = anomaly_evts[0]
    payload = {
        **asdict(ae),
        "classification": ae.metadata.get("classification", "event_journal"),
        "provenance": ae.metadata.get("provenance", "unit-test"),
        "redacted": False,
    }
    validate_schema("memory_event.schema.json", payload)


def test_self_model_status_healthy(tmp_path) -> None:
    """status returns healthy when all sources score 1.0."""
    sm = SelfModel(state_dir=str(tmp_path))
    sm.register_source(_FakeSource("a", {"ok": 1.0}))
    sm.register_source(_FakeSource("b", {"ok": 1.0}))
    sm.tick()
    assert sm.status == "healthy"


def test_self_model_status_degraded(tmp_path) -> None:
    """status returns degraded when scores are mixed."""
    sm = SelfModel(state_dir=str(tmp_path))
    sm.register_source(_FakeSource("a", {"ok": 0.5}))
    sm.register_source(_FakeSource("b", {"ok": 0.3}))
    sm.tick()
    # mean = 0.4, health_ratio > 0.0 → degraded
    assert sm.status == "degraded"


def test_self_model_multiple_ticks_trend(tmp_path) -> None:
    """Multiple ticks accumulate health history and compute trends."""
    sm = SelfModel(state_dir=str(tmp_path))
    src = _FakeSource("planner", {"success_rate": 0.2})
    sm.register_source(src)

    for v in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        src.set_metrics({"success_rate": v})
        sm.tick()

    snap = sm.snapshot()
    assert snap is not None
    trend = snap.node_trends.get("planner", 0.0)
    # Improving trend should be positive
    assert trend > 0.0
