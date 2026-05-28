"""Concept graph builder — extract concepts from PerceivedText and build
a shared concept map across modules. Filters stopwords and single-module
singletons.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from nodes.sensory_node import PerceivedText

STOP_WORDS: set[str] = {
    "the",
    "a",
    "an",
    "is",
    "in",
    "of",
    "to",
    "and",
    "or",
    "for",
    "with",
    "that",
    "this",
    "it",
    "be",
    "are",
    "was",
}


def _tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumeric, filter stopwords and short tokens."""
    tokens = re.findall(r"[a-z]{3,}", text.lower())
    return [t for t in tokens if t not in STOP_WORDS]


@dataclass
class ConceptNode:
    """A shared concept appearing in one or more modules."""

    concept: str             # normalized token (lowercased, stripped)
    modules: set[str]        # source_ids where this concept appears
    frequency: int           # total occurrences across all modules


@dataclass
class ConceptGraph:
    """Shared concept map over PerceivedText from multiple modules."""

    nodes: dict[str, ConceptNode]        # concept → ConceptNode
    module_index: dict[str, set[str]]    # source_id → set of concepts


class ConceptGraphBuilder:
    """Build a concept graph from a list of PerceivedText entries."""

    def build(self, perceived_list: list[PerceivedText]) -> ConceptGraph:
        """Tokenize each PerceivedText, build concept→modules mapping.

        Filters out concepts that appear in only 1 module AND have
        frequency < 2.
        """
        # concept → {set of source_ids}
        concept_modules: dict[str, set[str]] = {}
        concept_freq: dict[str, int] = {}

        for perceived in perceived_list:
            tokens = _tokenize(perceived.content)
            sid = perceived.source_id
            for token in tokens:
                if token not in concept_modules:
                    concept_modules[token] = set()
                    concept_freq[token] = 0
                concept_modules[token].add(sid)
                concept_freq[token] += 1

        # Build module_index: source_id → set of concepts
        module_index: dict[str, set[str]] = {}
        for concept, modules in concept_modules.items():
            for module_id in modules:
                if module_id not in module_index:
                    module_index[module_id] = set()
                module_index[module_id].add(concept)

        # Filter: keep concepts appearing in ≥2 modules OR freq ≥ 2
        nodes: dict[str, ConceptNode] = {}
        for concept, modules in concept_modules.items():
            if len(modules) >= 2 or concept_freq[concept] >= 2:
                nodes[concept] = ConceptNode(
                    concept=concept,
                    modules=modules,
                    frequency=concept_freq[concept],
                )

        return ConceptGraph(nodes=nodes, module_index=module_index)

    def top_concepts(self, graph: ConceptGraph, n: int = 20) -> list[ConceptNode]:
        """Return top N concepts sorted by frequency descending."""
        return sorted(graph.nodes.values(), key=lambda c: c.frequency, reverse=True)[:n]
