"""Top-level CoherenceGraph orchestrator.

Wires the full pipeline: load YAML graph → read live seed values from
world_snapshot.json → propagate → compute CoherenceIndex(t) → write
coherence_index back into the snapshot.

Exposes tick() for periodic updates and simulate() for counterfactual
what-if analysis.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from core.coherence.coherence_index import CoherenceIndexCalculator, CoherenceReport
from core.coherence.do_operator import DoIntervention, DoOperator
from core.coherence.graph_loader import CoherenceGraphDef, load_graph
from core.coherence.propagation import TopologicalPropagator

if TYPE_CHECKING:
    from core.self_model.world_snapshot import SnapshotWriter


class CoherenceGraph:
    """Orchestrate coherence graph propagation and snapshot integration."""

    def __init__(
        self,
        config_path: str | Path = "config/coherence_graph.yaml",
        snapshot_path: str | Path = "state/world_snapshot.json",
        snapshot_writer: SnapshotWriter | None = None,
    ) -> None:
        self._config_path = Path(config_path)
        self._snapshot_path = Path(snapshot_path)
        self._snapshot_writer = snapshot_writer

        self._graph_def: CoherenceGraphDef = load_graph(self._config_path)
        self._propagator = TopologicalPropagator(self._graph_def)
        self._calculator = CoherenceIndexCalculator(self._propagator.inbound_weight_sum)
        self._do_operator = DoOperator(self._graph_def, self._propagator)

    @property
    def graph_def(self) -> CoherenceGraphDef:
        return self._graph_def

    def tick(self) -> CoherenceReport:
        """Run one coherence cycle.

        1. Read live seed values from world_snapshot.json
        2. Forward-propagate through the DAG
        3. Compute CoherenceIndex(t) report
        4. If snapshot_writer is configured, update coherence_index in
           world_snapshot.json and re-write atomically
        5. Return the report
        """
        seed_values = self._read_seed_values()
        propagated = self._propagator.propagate(seed_values)
        report = self._calculator.compute(propagated)

        # Write coherence_index back into the snapshot
        if self._snapshot_writer is not None:
            self._update_snapshot_coherence(report.coherence_index)

        return report

    def simulate(
        self, intervention: DoIntervention
    ) -> tuple[CoherenceReport, dict[str, float]]:
        """Run a counterfactual: fix a node to a value, sever its inbound
        edges, propagate, compare against baseline.

        Returns (intervened_report, delta_per_node).
        Does NOT write to disk — pure read-only counterfactual.
        """
        seed_values = self._read_seed_values()
        baseline = self._propagator.propagate(seed_values)
        intervened = self._do_operator.apply(seed_values, intervention)
        delta = self._do_operator.compare(baseline, intervened)
        report = self._calculator.compute(intervened)
        return report, delta

    def reload_config(self) -> None:
        """Re-parse the YAML graph without restarting — hot-reload support."""
        self._graph_def = load_graph(self._config_path)
        self._propagator = TopologicalPropagator(self._graph_def)
        self._calculator = CoherenceIndexCalculator(self._propagator.inbound_weight_sum)
        self._do_operator = DoOperator(self._graph_def, self._propagator)

    # ── Internal ──────────────────────────────────────────────────────────

    def _read_seed_values(self) -> dict[str, float]:
        """Extract node health scores from world_snapshot.json as seed values."""
        if not self._snapshot_path.exists():
            return {}
        try:
            data = json.loads(self._snapshot_path.read_text(encoding="utf-8"))
            node_health = data.get("node_health", {})
            if isinstance(node_health, dict):
                return {k: float(v) for k, v in node_health.items()}
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        return {}

    def _update_snapshot_coherence(self, coherence_index: float) -> None:
        """Read snapshot, set coherence_index, write back atomically."""
        if self._snapshot_writer is None:
            return
        from core.self_model.world_snapshot import WorldSnapshot

        current = self._snapshot_writer.read_snapshot()
        if current is None:
            return
        updated = WorldSnapshot(
            timestamp=current.timestamp,
            node_health=dict(current.node_health),
            node_trends=dict(current.node_trends),
            system_health_ratio=current.system_health_ratio,
            anomaly_count=current.anomaly_count,
            coherence_index=round(coherence_index, 6),
        )
        self._snapshot_writer.write(updated)
