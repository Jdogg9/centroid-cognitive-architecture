"""Centroid Module Coherence Graph — causal DAG for runtime coherence tracking.

Measures how the five core modules (memory, router, planner, safety,
self_model) influence each other. Live seed values come from
state/world_snapshot.json. CoherenceIndex(t) is the weighted mean
of all propagated node scores.
"""

from core.coherence.coherence_graph import CoherenceGraph
from core.coherence.coherence_index import CoherenceIndexCalculator, CoherenceReport
from core.coherence.do_operator import DoIntervention, DoOperator
from core.coherence.graph_loader import CoherenceGraphDef, EdgeDef, NodeDef, load_graph
from core.coherence.propagation import TopologicalPropagator

__all__ = [
    "CoherenceGraph",
    "CoherenceIndexCalculator",
    "CoherenceReport",
    "DoIntervention",
    "DoOperator",
    "CoherenceGraphDef",
    "EdgeDef",
    "NodeDef",
    "load_graph",
    "TopologicalPropagator",
]
