"""Pearl-style do-operator for counterfactual interventions on the coherence graph.

Sever inbound edges to a target node, fix its value, propagate forward,
compare the resulting state against baseline.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

from core.coherence.graph_loader import CoherenceGraphDef, EdgeDef
from core.coherence.propagation import TopologicalPropagator


@dataclass
class DoIntervention:
    node_id: str
    fixed_value: float  # the value to hold this node at


class DoOperator:
    """Apply do(X=x) interventions and compare with baseline."""

    def __init__(
        self,
        graph_def: CoherenceGraphDef,
        propagator: TopologicalPropagator,
    ) -> None:
        self._graph = graph_def
        self._propagator = propagator

    def apply(
        self,
        seed_values: dict[str, float],
        intervention: DoIntervention,
    ) -> dict[str, float]:
        """Run a counterfactual: sever inbound edges to node_id, fix its
        value, and propagate forward.

        The original graph_def is never mutated — edges are filtered
        per-call.
        """
        values = dict(seed_values)
        values[intervention.node_id] = intervention.fixed_value

        # Build a filtered graph: remove all edges INTO the intervened node
        filtered_edges: list[EdgeDef] = []
        for e in self._graph.edges:
            if e.to_node == intervention.node_id:
                continue  # sever inbound edge
            filtered_edges.append(e)

        filtered_def = CoherenceGraphDef(
            nodes=list(self._graph.nodes),
            edges=filtered_edges,
        )

        # Create a fresh propagator for the filtered graph
        filtered_prop = TopologicalPropagator(filtered_def)
        return filtered_prop.propagate(values)

    def compare(
        self,
        baseline: dict[str, float],
        intervened: dict[str, float],
    ) -> dict[str, float]:
        """Compute delta per node: intervened - baseline.

        Positive = intervention increased coherence for that node.
        """
        deltas: dict[str, float] = {}
        all_nodes = set(baseline) | set(intervened)
        for node_id in sorted(all_nodes):
            deltas[node_id] = round(
                intervened.get(node_id, 0.0) - baseline.get(node_id, 0.0), 6
            )
        return deltas
