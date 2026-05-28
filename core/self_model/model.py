"""Self-model: runtime health, anomaly detection, world snapshots.

SelfModelSnapshot (original): lightweight dataclass for node ratio health.
SelfModel (new): full pipeline — aggregator → health scorer → anomaly detector
→ snapshot writer. With zero sources, health_ratio/status behave identically
to the original implementation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from core.memory.store import MemoryStore
from core.self_model.anomaly_detector import AnomalyDetector, AnomalyEvent
from core.self_model.health_scorer import HealthScorer
from core.self_model.telemetry_aggregator import TelemetryAggregator, TelemetrySource
from core.self_model.world_snapshot import SnapshotWriter, WorldSnapshot


# ── Original (preserved) ──────────────────────────────────────────────────


@dataclass
class SelfModelSnapshot:
    """Runtime self-model: health and state, not subjective awareness."""

    nodes_alive: int
    nodes_total: int
    active_goals: list[str] = field(default_factory=list)
    known_failures: list[str] = field(default_factory=list)

    @property
    def health_ratio(self) -> float:
        if self.nodes_total <= 0:
            return 0.0
        return self.nodes_alive / self.nodes_total

    @property
    def status(self) -> str:
        if self.health_ratio == 1.0:
            return "healthy"
        if self.health_ratio > 0.0:
            return "degraded"
        return "critical"


# ── Full pipeline self-model ──────────────────────────────────────────────


class SelfModel:
    """Live self-model: telemetry aggregation → health scoring → anomaly
    detection → world snapshot persistence.

    When no TelemetrySource is registered, health_ratio and status fall
    back to the original SelfModelSnapshot behavior (nodes_alive=0, ratio=0.0,
    status="critical").
    """

    def __init__(
        self,
        memory_store: MemoryStore | None = None,
        state_dir: str = "state",
        *,
        warn_threshold: float = 2.0,
        critical_threshold: float = 3.5,
        trend_window: int = 5,
    ) -> None:
        self._memory_store = memory_store
        self._state_dir = state_dir
        self._aggregator = TelemetryAggregator()
        self._health_scorer = HealthScorer(trend_window=trend_window)
        self._anomaly_detector = AnomalyDetector(
            warn_threshold=warn_threshold,
            critical_threshold=critical_threshold,
        )
        self._snapshot_writer = SnapshotWriter(state_dir=state_dir)
        self._anomaly_count: int = 0

    def register_source(self, source: TelemetrySource) -> None:
        """Register a telemetry source for periodic collection."""
        self._aggregator.register(source)

    def unregister_source(self, source_id: str) -> None:
        """Remove a registered source."""
        self._aggregator.unregister(source_id)

    def tick(self) -> WorldSnapshot:
        """Run one self-model cycle.

        1. Collect all telemetry
        2. Update health scores per source
        3. Detect anomalies
        4. Append anomalies to memory_store (if provided)
        5. Write world snapshot
        6. Return the snapshot
        """
        collected = self._aggregator.collect()

        node_health_scores: dict[str, float] = {}
        node_trends: dict[str, float] = {}

        for source_id, metrics in collected.items():
            health = self._health_scorer.update(source_id, metrics)
            node_health_scores[source_id] = health.score
            node_trends[source_id] = health.trend

            # Anomaly detection
            anomalies = self._anomaly_detector.update(source_id, metrics)
            if anomalies and self._memory_store is not None:
                for ae in anomalies:
                    self._anomaly_count += 1
                    self._memory_store.append(
                        _anomaly_to_event(ae),
                    )

        system_ratio = self._health_scorer.system_health_ratio()

        snapshot = WorldSnapshot(
            timestamp=time.time(),
            node_health=node_health_scores,
            node_trends=node_trends,
            system_health_ratio=round(system_ratio, 4),
            anomaly_count=self._anomaly_count,
            coherence_index=None,  # Phase 2
        )

        self._snapshot_writer.write(snapshot)
        return snapshot

    @property
    def health_ratio(self) -> float:
        """System health ratio: mean score across all registered sources.

        Falls back to 0.0 when no sources are registered (consistent
        with the original SelfModelSnapshot behavior at nodes_total=0).
        """
        return self._health_scorer.system_health_ratio()

    @property
    def status(self) -> str:
        """Health status string: healthy, degraded, or critical."""
        if self._aggregator.source_ids:
            hr = self.health_ratio
        else:
            hr = 0.0  # no sources = critical (matches original)
        if hr == 1.0:
            return "healthy"
        if hr > 0.0:
            return "degraded"
        return "critical"

    @property
    def anomaly_count(self) -> int:
        """Total anomalies detected across all ticks."""
        return self._anomaly_count

    def snapshot(self) -> WorldSnapshot | None:
        """Read the most recently persisted snapshot (None if never written)."""
        return self._snapshot_writer.read_snapshot()


# ── Internal ──────────────────────────────────────────────────────────────


def _anomaly_to_event(ae: AnomalyEvent):
    """Convert an AnomalyEvent into a schema-valid memory Event."""
    from core.memory.store import Event

    return Event(
        event_type="anomaly",
        content=f"{ae.severity}: {ae.source_id}/{ae.field} z={ae.z_score:.2f} (observed {ae.observed}, mean {ae.mean})",
        source="self_model",
        metadata={
            "classification": "event_journal",
            "source_id": ae.source_id,
            "field": ae.field,
            "z_score": str(ae.z_score),
            "severity": ae.severity,
            "observed": str(ae.observed),
            "mean": str(ae.mean),
            "timestamp": str(ae.timestamp),
        },
    )
