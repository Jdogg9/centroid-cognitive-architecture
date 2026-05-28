"""Cross-module bridge detection — find concept overlaps between modules
that have no direct edge in the coherence graph. These are "implicit
bridges" suggesting latent architectural relationships.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from core.fusion.concept_graph import ConceptGraph

if TYPE_CHECKING:
    from core.coherence.graph_loader import CoherenceGraphDef


@dataclass
class BridgeCandidate:
    """A cross-module bridge found via shared concepts."""

    concept: str
    module_a: str
    module_b: str
    shared_concept_count: int       # how many concepts link this pair
    bridge_score: float             # 0.0 – 1.0
    detected_at: float


class BridgeDetector:
    """Detect bridges between modules based on shared concept vocabularies."""

    def __init__(
        self,
        coherence_graph_def: CoherenceGraphDef | None = None,
    ) -> None:
        self._coherence_graph = coherence_graph_def
        # Build edge lookup for implicit bridge detection
        self._edge_pairs: set[tuple[str, str]] = set()
        if coherence_graph_def is not None:
            for edge in coherence_graph_def.edges:
                self._edge_pairs.add((edge.from_node, edge.to_node))
                self._edge_pairs.add((edge.to_node, edge.from_node))

    def detect(self, concept_graph: ConceptGraph) -> list[BridgeCandidate]:
        """Find all module pairs that share concepts.

        Score = shared_count / min(|module_a concepts|, |module_b concepts|).
        """
        module_ids = sorted(concept_graph.module_index.keys())
        candidates: list[BridgeCandidate] = []

        for i, mod_a in enumerate(module_ids):
            for mod_b in module_ids[i + 1:]:
                concepts_a = concept_graph.module_index.get(mod_a, set())
                concepts_b = concept_graph.module_index.get(mod_b, set())
                shared = concepts_a & concepts_b

                if not shared:
                    continue

                shared_count = len(shared)
                max_possible = min(len(concepts_a), len(concepts_b))
                bridge_score = shared_count / max_possible if max_possible > 0 else 0.0

                # Take the first shared concept as the representative
                representative = sorted(shared)[0]

                candidates.append(
                    BridgeCandidate(
                        concept=representative,
                        module_a=mod_a,
                        module_b=mod_b,
                        shared_concept_count=shared_count,
                        bridge_score=round(bridge_score, 6),
                        detected_at=time.time(),
                    )
                )

        candidates.sort(key=lambda c: c.bridge_score, reverse=True)
        return candidates

    def implicit_bridges(
        self, candidates: list[BridgeCandidate]
    ) -> list[BridgeCandidate]:
        """Filter to bridges NOT covered by a coherence graph edge."""
        return [
            c for c in candidates
            if (c.module_a, c.module_b) not in self._edge_pairs
        ]
