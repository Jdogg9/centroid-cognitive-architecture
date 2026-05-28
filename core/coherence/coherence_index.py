"""Coherence Index computation from propagated graph state.

CoherenceIndex(t) is the weighted mean of all node scores, where each
node is weighted by the sum of its inbound edge weights (more
depended-upon nodes count more).
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class CoherenceReport:
    """A complete coherence snapshot for the current tick."""

    timestamp: float
    node_scores: dict[str, float]     # propagated values per node
    coherence_index: float             # scalar 0.0 – 1.0
    weakest_node: str                  # node_id with lowest score
    strongest_node: str                # node_id with highest score


class CoherenceIndexCalculator:
    """Compute CoherenceIndex(t) from propagated node values."""

    def __init__(self, inbound_weight_sum: dict[str, float]) -> None:
        """inbound_weight_sum: {node_id: sum_of_inbound_edge_weights}
        from TopologicalPropagator. Nodes with no inbound edges default to 1.0.
        """
        self._weights = dict(inbound_weight_sum)

    def compute(self, propagated: dict[str, float]) -> CoherenceReport:
        """Compute weighted coherence index from propagated values."""
        if not propagated:
            return CoherenceReport(
                timestamp=time.time(),
                node_scores={},
                coherence_index=0.0,
                weakest_node="",
                strongest_node="",
            )

        total_weight = 0.0
        weighted_sum = 0.0

        for node_id, score in propagated.items():
            w = self._weights.get(node_id, 1.0)
            weighted_sum += score * w
            total_weight += w

        coherence_index = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Find weakest and strongest
        sorted_nodes = sorted(propagated.items(), key=lambda x: x[1])
        weakest = sorted_nodes[0][0]
        strongest = sorted_nodes[-1][0]

        return CoherenceReport(
            timestamp=time.time(),
            node_scores=dict(propagated),
            coherence_index=round(max(0.0, min(1.0, coherence_index)), 6),
            weakest_node=weakest,
            strongest_node=strongest,
        )
