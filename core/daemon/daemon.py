"""Top-level daemon wiring for the Centroid architecture."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from core.coherence import CoherenceGraph
from core.daemon.cycle import CycleResult, CycleRunner
from core.daemon.scheduler import CycleScheduler, SchedulerConfig
from core.memory import MemoryStore
from core.planner.calibration import CalibrationStore
from core.planner.feedback_loop import ForecastFeedbackLoop
from core.planner.forecast import ForecastGenerator
from core.planner.plan_tree import PlanTree
from core.self_model import SelfModel
from core.self_model.world_snapshot import SnapshotWriter
from nodes.sensory_node import SensoryPipeline


@dataclass
class DaemonConfig:
    tick_interval_s: float = 5.0
    max_cycles: int | None = None
    startup_delay_s: float = 0.0
    state_dir: str = "state/"
    coherence_graph_path: str = "config/coherence_graph.yaml"
    memory_store_path: str = "state/memory.jsonl"
    enable_sensory: bool = True
    enable_coherence: bool = True
    enable_forecast: bool = True
    enable_feedback: bool = True


class CentroidDaemon:
    """Ready-to-run daemon composed from optional Centroid modules."""

    def __init__(
        self,
        config: DaemonConfig,
        *,
        runner: CycleRunner | None = None,
        scheduler: CycleScheduler | None = None,
    ) -> None:
        self.config = config
        self.runner = runner or CycleRunner()
        self.scheduler = scheduler or CycleScheduler(
            self.runner,
            SchedulerConfig(
                tick_interval_s=config.tick_interval_s,
                max_cycles=config.max_cycles,
                startup_delay_s=config.startup_delay_s,
            ),
        )

    @classmethod
    def from_config(cls, config: DaemonConfig) -> "CentroidDaemon":
        state_dir = Path(config.state_dir)
        state_dir.mkdir(parents=True, exist_ok=True)
        memory_store = MemoryStore(Path(config.memory_store_path))
        self_model = SelfModel(memory_store=memory_store, state_dir=str(state_dir))

        snapshot_writer = SnapshotWriter(state_dir=state_dir)
        coherence_graph = None
        if config.enable_coherence:
            coherence_graph = CoherenceGraph(
                config_path=config.coherence_graph_path,
                snapshot_path=state_dir / "world_snapshot.json",
                snapshot_writer=snapshot_writer,
            )

        calibration_store = None
        forecast_generator = None
        feedback_loop = None
        if config.enable_forecast or config.enable_feedback:
            calibration_store = CalibrationStore(state_dir / "calibration.json")
        if config.enable_forecast:
            forecast_generator = ForecastGenerator(fields=["system_health_ratio"])
        if config.enable_feedback:
            feedback_loop = ForecastFeedbackLoop(
                calibration=calibration_store,
                plan_tree=PlanTree(state_path=state_dir / "plan_tree.json"),
            )

        sensory_pipeline = None
        if config.enable_sensory:
            sensory_pipeline = SensoryPipeline(core_root="core/")

        runner = CycleRunner(
            memory_store=memory_store,
            self_model=self_model,
            coherence_graph=coherence_graph,
            forecast_generator=forecast_generator,
            feedback_loop=feedback_loop,
            sensory_pipeline=sensory_pipeline,
            calibration_store=calibration_store,
        )
        return cls(config, runner=runner)

    def run(self) -> None:
        self.scheduler.start()

    def run_cycles(self, n: int) -> list[CycleResult]:
        return [self.runner.run(i) for i in range(n)]


def load_config(path: str | Path | None) -> DaemonConfig:
    if path is not None:
        config_path = Path(path)
        if config_path.exists():
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            return DaemonConfig(**raw)
        if str(config_path) == "config/daemon.yaml":
            config_path.parent.mkdir(parents=True, exist_ok=True)
            defaults = DaemonConfig()
            config_path.write_text(_config_yaml(defaults), encoding="utf-8")
            return defaults
    return DaemonConfig()


def _config_yaml(config: DaemonConfig) -> str:
    max_cycles = "null" if config.max_cycles is None else str(config.max_cycles)
    return (
        f"tick_interval_s: {config.tick_interval_s}\n"
        f"max_cycles: {max_cycles}\n"
        f"startup_delay_s: {config.startup_delay_s}\n"
        f"state_dir: \"{config.state_dir}\"\n"
        f"coherence_graph_path: \"{config.coherence_graph_path}\"\n"
        f"memory_store_path: \"{config.memory_store_path}\"\n"
        f"enable_sensory: {str(config.enable_sensory).lower()}\n"
        f"enable_coherence: {str(config.enable_coherence).lower()}\n"
        f"enable_forecast: {str(config.enable_forecast).lower()}\n"
        f"enable_feedback: {str(config.enable_feedback).lower()}\n"
    )
