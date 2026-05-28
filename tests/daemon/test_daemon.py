from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.memory.store import MemoryStore


class DummySelfModel:
    def __init__(self, *, fail: bool = False):
        self.fail = fail

    def tick(self):
        if self.fail:
            raise RuntimeError("self-model boom")
        from core.self_model.world_snapshot import WorldSnapshot

        return WorldSnapshot(
            timestamp=1.0,
            node_health={"alpha": 0.8, "beta": 0.4},
            node_trends={"alpha": 0.0, "beta": -0.1},
            system_health_ratio=0.6,
            anomaly_count=2,
            coherence_index=None,
        )


class DummyCoherenceGraph:
    def tick(self):
        from core.coherence.coherence_index import CoherenceReport

        return CoherenceReport(
            timestamp=1.0,
            node_scores={"alpha": 0.8},
            coherence_index=0.75,
            weakest_node="alpha",
            strongest_node="alpha",
        )


class DummyForecastGenerator:
    def __init__(self):
        self.calls = []

    def generate(self, current_values, calibration_store):
        self.calls.append((current_values, calibration_store))
        from core.planner.forecast import Forecast

        return [
            Forecast(
                horizon="short",
                cycle_distance=1,
                predictions={"alpha": 0.7},
                confidence=0.5,
                generated_at=1.0,
                forecast_id="forecast-1",
            )
        ]


class DummyFeedbackLoop:
    def __init__(self):
        self.registered = []
        self.resolved = []

    def register(self, forecast):
        self.registered.append(forecast)

    def resolve(self, actual_values, cycle_number=None):
        self.resolved.append((actual_values, cycle_number))
        return []


class DummySensoryPipeline:
    def __init__(self):
        self.calls = 0

    def run_startup_scan(self):
        self.calls += 1
        return []


def test_cycle_runner_no_modules():
    from core.daemon import CycleRunner

    result = CycleRunner().run(0)

    assert result.cycle_number == 0
    assert result.errors == []
    assert result.self_model_snapshot is None
    assert result.coherence_report is None
    assert result.forecasts is None
    assert result.feedback_results is None


def test_cycle_runner_step_error_continues():
    from core.daemon import CycleRunner

    result = CycleRunner(self_model=DummySelfModel(fail=True), sensory_pipeline=DummySensoryPipeline()).run(0)

    assert result.completed_at >= result.started_at
    assert any("self-model boom" in error for error in result.errors)


def test_cycle_runner_memory_append(tmp_path):
    from core.daemon import CycleRunner

    store = MemoryStore(tmp_path / "memory.jsonl")
    result = CycleRunner(memory_store=store, self_model=DummySelfModel()).run(3)

    events = store.tail(1)
    assert result.errors == []
    assert events[0].event_type == "cycle_complete"
    assert events[0].source == "daemon"
    metadata = events[0].metadata
    assert metadata["cycle"] == "3"
    assert metadata["anomaly_count"] == "2"


def test_cycle_runner_sensory_once():
    from core.daemon import CycleRunner

    sensory = DummySensoryPipeline()
    runner = CycleRunner(sensory_pipeline=sensory)

    runner.run(0)
    runner.run(1)

    assert sensory.calls == 1


def test_cycle_runner_result_fields():
    from core.daemon import CycleRunner

    result = CycleRunner().run(0)

    assert result.started_at > 0
    assert result.completed_at >= result.started_at
    assert result.duration_s > 0
    assert isinstance(result.errors, list)


def test_scheduler_stop_flag():
    from core.daemon import CycleScheduler, SchedulerConfig

    class StoppingRunner:
        def __init__(self):
            self.calls = 0
            self.scheduler = None

        def run(self, cycle_number):
            self.calls += 1
            self.scheduler.stop()
            from core.daemon import CycleResult

            return CycleResult(cycle_number, 1.0, 1.1, 0.1, None, None, None, None, 0, [])

    runner = StoppingRunner()
    scheduler = CycleScheduler(runner, SchedulerConfig(tick_interval_s=0.0))
    runner.scheduler = scheduler
    scheduler.start()

    assert runner.calls == 1


def test_scheduler_max_cycles():
    from core.daemon import CycleResult, CycleScheduler, SchedulerConfig

    class Runner:
        def __init__(self):
            self.calls = []

        def run(self, cycle_number):
            self.calls.append(cycle_number)
            return CycleResult(cycle_number, 1.0, 1.1, 0.1, None, None, None, None, 0, [])

    runner = Runner()
    CycleScheduler(runner, SchedulerConfig(tick_interval_s=0.0, max_cycles=3)).start()

    assert runner.calls == [0, 1, 2]


def test_scheduler_no_drift(monkeypatch):
    from core.daemon import CycleResult, CycleScheduler, SchedulerConfig

    monotonic_values = iter([0.0, 0.25, 1.0, 1.75])
    sleeps = []
    monkeypatch.setattr("core.daemon.scheduler.time.monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr("core.daemon.scheduler.time.sleep", lambda seconds: sleeps.append(seconds))

    class Runner:
        def run(self, cycle_number):
            return CycleResult(cycle_number, 1.0, 1.1, 0.1, None, None, None, None, 0, [])

    CycleScheduler(Runner(), SchedulerConfig(tick_interval_s=1.0, max_cycles=2)).start()

    assert sleeps == [0.75]


def test_daemon_config_defaults():
    from core.daemon import DaemonConfig

    config = DaemonConfig()

    assert config.tick_interval_s == 5.0
    assert config.max_cycles is None
    assert config.startup_delay_s == 0.0
    assert config.state_dir == "state/"
    assert config.coherence_graph_path == "config/coherence_graph.yaml"
    assert config.memory_store_path == "state/memory.jsonl"
    assert config.enable_sensory is True
    assert config.enable_coherence is True
    assert config.enable_forecast is True
    assert config.enable_feedback is True


def test_daemon_config_from_yaml(tmp_path):
    from core.daemon import load_config

    path = tmp_path / "daemon.yaml"
    path.write_text("tick_interval_s: 2.5\nmax_cycles: 7\nenable_sensory: false\n", encoding="utf-8")

    config = load_config(path)

    assert config.tick_interval_s == 2.5
    assert config.max_cycles == 7
    assert config.enable_sensory is False


def test_daemon_run_cycles(tmp_path):
    from core.daemon import CentroidDaemon, CycleRunner, DaemonConfig

    runner = CycleRunner(memory_store=MemoryStore(tmp_path / "memory.jsonl"))
    daemon = CentroidDaemon(DaemonConfig(max_cycles=2), runner=runner)

    results = daemon.run_cycles(2)

    assert len(results) == 2
    assert [r.cycle_number for r in results] == [0, 1]


def test_daemon_dry_run_exit():
    completed = subprocess.run(
        [sys.executable, "examples/run_daemon.py", "--dry-run"],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert "cycle=0" in completed.stdout
    assert "cycle=1" in completed.stdout
    assert "cycle=2" in completed.stdout
