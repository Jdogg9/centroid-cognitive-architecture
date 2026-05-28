"""Topological forward propagation through a coherence DAG.

Non-feedback edges are topologically sorted (Kahn's algorithm) and
applied in order. Feedback edges are applied in a separate post-pass
to break cycles. All output values are clamped to [0.0, 1.0].
"""

from __future__ import annotations

from collections import deque

from core.coherence.graph_loader import FEEDBACK_TYPE, CoherenceGraphDef


class TopologicalPropagator:
    """Propagate values forward through a directed coherence graph."""

    def __init__(self, graph_def: CoherenceGraphDef) -> None:
        self._graph = graph_def
        self._node_ids = {n.node_id for n in graph_def.nodes}

        # Separate feedback edges for post-pass
        self._feedback_edges = [e for e in graph_def.edges if e.edge_type == FEEDBACK_TYPE]
        self._fwd_edges = [e for e in graph_def.edges if e.edge_type != FEEDBACK_TYPE]

        # Compute topological order once (Kahn's, on forward edges only)
        self._topo_order = self._kahn()

        # Precompute inbound edge weight sums per node for CoherenceIndex weighting
        self._inbound_weight_sum: dict[str, float] = {}
        for node_id in self._node_ids:
            total = sum(e.weight for e in self._fwd_edges if e.to_node == node_id)
            # Also count feedback edges for completeness
            total += sum(e.weight for e in self._feedback_edges if e.to_node == node_id)
            self._inbound_weight_sum[node_id] = total if total > 0 else 1.0

    @property
    def node_ids(self) -> set[str]:
        return set(self._node_ids)

    @property
    def inbound_weight_sum(self) -> dict[str, float]:
        return dict(self._inbound_weight_sum)

    def topological_order(self) -> list[str]:
        """Return node IDs in propagation order (feedback edges excluded)."""
        return list(self._topo_order)

    def propagate(self, seed_values: dict[str, float]) -> dict[str, float]:
        """Propagate seed values through the DAG.

        Args:
            seed_values: {node_id: live_health_score} from world_snapshot.

        Returns:
            {node_id: propagated_value} for all nodes, clamped to [0, 1].
        """
        # Initialize: use seed_values, default to 0.5 for missing nodes
        values: dict[str, float] = {}
        for node_id in self._node_ids:
            if node_id in seed_values:
                values[node_id] = float(seed_values[node_id])
            else:
                values[node_id] = 0.5

        # Forward pass: apply non-feedback edges in topological order
        for node_id in self._topo_order:
            for edge in self._fwd_edges:
                if edge.to_node != node_id:
                    continue
                if edge.from_node not in values:
                    continue
                upstream = values[edge.from_node]
                downstream = values[edge.to_node]

                values[node_id] = _apply_edge(edge.edge_type, upstream, downstream, edge.weight)

        # Post-pass: feedback edges applied once
        for edge in self._feedback_edges:
            if edge.from_node in values and edge.to_node in values:
                upstream = values[edge.from_node]
                downstream = values[edge.to_node]
                values[edge.to_node] = _apply_feedback(upstream, downstream, edge.weight)

        # Clamp all outputs
        return {nid: max(0.0, min(1.0, round(v, 6))) for nid, v in values.items()}

    def _kahn(self) -> list[str]:
        """Kahn's algorithm for topological sort on forward edges only."""
        in_degree: dict[str, int] = {nid: 0 for nid in self._node_ids}
        children: dict[str, list[str]] = {nid: [] for nid in self._node_ids}

        for edge in self._fwd_edges:
            in_degree[edge.to_node] += 1
            children[edge.from_node].append(edge.to_node)

        queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
        order: list[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for child in children[node]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if len(order) != len(self._node_ids):
            # Cycle detected in non-feedback edges — fall back to declaration order
            return [n.node_id for n in self._graph.nodes]

        return order


# ── Edge semantics ────────────────────────────────────────────────────────


def _apply_edge(edge_type: str, upstream: float, downstream: float, weight: float) -> float:
    """Apply a single edge's transformation.

    All edge types clamp output to [0.0, 1.0] at the call site (propagate()).
    """
    if edge_type in ("multiplicative_factor", "proportional", "modulates"):
        return upstream * weight
    elif edge_type in ("additive_factor", "reinforces"):
        return downstream + upstream * weight
    elif edge_type == "suppresses":
        return downstream * (1.0 - upstream * weight)
    else:
        return downstream  # unknown, pass through


def _apply_feedback(upstream: float, downstream: float, weight: float) -> float:
    """Feedback is a gentle additive correction — doesn't dominate."""
    return downstream + (upstream - 0.5) * weight * 0.05
