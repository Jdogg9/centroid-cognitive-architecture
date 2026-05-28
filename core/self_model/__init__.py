"""Centroid self-model: health, telemetry, anomaly detection, and world snapshots."""

from core.self_model.anomaly_detector import AnomalyDetector, AnomalyEvent
from core.self_model.health_scorer import HealthScorer, NodeHealth
from core.self_model.model import SelfModel, SelfModelSnapshot
from core.self_model.telemetry_aggregator import TelemetryAggregator, TelemetrySource
from core.self_model.world_snapshot import SnapshotWriter, WorldSnapshot

__all__ = [
    # Original
    "SelfModelSnapshot",
    # Full pipeline
    "SelfModel",
    # Telemetry
    "TelemetryAggregator",
    "TelemetrySource",
    # Health
    "HealthScorer",
    "NodeHealth",
    # Anomaly
    "AnomalyDetector",
    "AnomalyEvent",
    # Snapshot
    "SnapshotWriter",
    "WorldSnapshot",
]
