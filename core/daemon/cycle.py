"""One synchronous daemon cycle for the Centroid architecture."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.coherence.coherence_index import CoherenceReport
from core.memory.store import Event, MemoryStore
from core.planner.feedback_loop import FeedbackResult, ForecastFeedbackLoop
from core.planner.forecast import Forecast, ForecastGenerator
from core.self_model.world_snapshot import WorldSnapshot


@dataclass
class CycleResult:
    cycle_number: int
    started_at: float
    completed_at: float
    duration_s: float
    self_model_snapshot: WorldSnapshot | None
    coherence_report: CoherenceReport | None
    forecasts: list[Forecast] | None
    feedback_results: list[FeedbackResult] | None
    anomaly_count: int
    errors: list[str]


class CycleRunner:
    """Run one full daemon tick with optional modules and isolated errors."""

    def __init__(
        self,
        memory_store: MemoryStore | None = None,
        self_model: Any | None = None,
        coherence_graph: Any | None = None,
        forecast_generator: ForecastGenerator | None = None,
        feedback_loop: ForecastFeedbackLoop | None = None,
        sensory_pipeline: Any | None = None,
        calibration_store: Any | None = None,
    ) -> None:
        self.memory_store = memory_store
        self.self_model = self_model
        self.coherence_graph = coherence_graph
        self.forecast_generator = forecast_generator
        self.feedback_loop = feedback_loop
        self.sensory_pipeline = sensory_pipeline
        self.calibration_store = calibration_store

    def run(self, cycle_number: int) -> CycleResult:
        started_at = time.time()
        errors: list[str] = []
        snapshot: WorldSnapshot | None = None
        report: CoherenceReport | None = None
        forecasts: list[Forecast] | None = None
        feedback_results: list[FeedbackResult] | None = None
        anomaly_count = 0

        if cycle_number == 0 and self.sensory_pipeline is not None:
            try:
                self.sensory_pipeline.run_startup_scan()
            except Exception as exc:  # noqa: BLE001 - daemon fault isolation
                errors.append(f"sensory: {exc}")

        if self.self_model is not None:
            try:
                snapshot = self.self_model.tick()
                anomaly_count = int(getattr(snapshot, "anomaly_count", 0))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"self_model: {exc}")

        current_values = self._current_values(snapshot)
        if self.coherence_graph is not None:
            try:
                self._seed_world_snapshot(snapshot)
                report = self.coherence_graph.tick()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"coherence: {exc}")

        if self.forecast_generator is not None:
            try:
                forecasts = self.forecast_generator.generate(current_values, self.calibration_store)
                if self.feedback_loop is not None:
                    for forecast in forecasts:
                        self.feedback_loop.register(forecast)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"forecast: {exc}")

        if self.feedback_loop is not None:
            try:
                try:
                    feedback_results = self.feedback_loop.resolve(current_values, cycle_number)
                except TypeError:
                    feedback_results = self.feedback_loop.resolve(current_values)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"feedback: {exc}")

        completed_at = time.time()
        duration_s = max(0.0, completed_at - started_at)
        if duration_s == 0.0:
            duration_s = 1e-9

        if self.memory_store is not None:
            try:
                self.memory_store.append(
                    Event(
                        event_type="cycle_complete",
                        content=f"cycle {cycle_number} completed in {duration_s:.6f}s",
                        source="daemon",
                        metadata={
                            "classification": "event_journal",
                            "cycle": str(cycle_number),
                            "duration_s": str(duration_s),
                            "coherence_index": "" if report is None else str(report.coherence_index),
                            "anomaly_count": str(anomaly_count),
                            "timestamp": str(completed_at),
                        },
                    )
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"memory: {exc}")

        return CycleResult(
            cycle_number=cycle_number,
            started_at=started_at,
            completed_at=completed_at,
            duration_s=duration_s,
            self_model_snapshot=snapshot,
            coherence_report=report,
            forecasts=forecasts,
            feedback_results=feedback_results,
            anomaly_count=anomaly_count,
            errors=errors,
        )

    @staticmethod
    def _current_values(snapshot: WorldSnapshot | None) -> dict[str, float]:
        if snapshot is None:
            return {}
        values = dict(snapshot.node_health)
        values["system_health_ratio"] = float(snapshot.system_health_ratio)
        return values

    @staticmethod
    def _seed_world_snapshot(snapshot: WorldSnapshot | None) -> None:
        """SelfModel.tick already writes the snapshot; this hook keeps ordering explicit."""
        if snapshot is None:
            return
        # Deliberately no extra write: SnapshotWriter ownership stays with SelfModel.
        Path("state").mkdir(exist_ok=True)
