from __future__ import annotations

import time

from core.coherence.graph_loader import CoherenceGraphDef, EdgeDef, NodeDef
from core.fusion import BridgeDetector, BridgeSynthesizer, ConceptGraph, ConceptGraphBuilder
from nodes.sensory_node import PerceivedText


def _perceived(source_id: str, content: str, source_kind: str = "code") -> PerceivedText:
    return PerceivedText(source_kind, content, source_id, time.time())


def _graph_with_shared_concepts() -> ConceptGraph:
    return ConceptGraphBuilder().build(
        [
            _perceived("module_a", "alpha bridge shared signal"),
            _perceived("module_b", "bridge shared beta signal"),
            _perceived("module_c", "gamma isolated gamma"),
        ]
    )


def test_concept_graph_builds() -> None:
    graph = _graph_with_shared_concepts()

    assert isinstance(graph, ConceptGraph)
    assert graph.nodes


def test_concept_graph_multi_module() -> None:
    graph = _graph_with_shared_concepts()

    assert graph.nodes["bridge"].modules == {"module_a", "module_b"}


def test_concept_graph_stopword_filtered() -> None:
    graph = ConceptGraphBuilder().build(
        [_perceived("module_a", "the and useful useful"), _perceived("module_b", "useful")]
    )

    assert "the" not in graph.nodes
    assert "and" not in graph.nodes


def test_concept_graph_frequency_filter() -> None:
    graph = ConceptGraphBuilder().build(
        [
            _perceived("module_a", "ephemeral repeated repeated"),
            _perceived("module_b", "stable stable"),
        ]
    )

    assert "ephemeral" not in graph.nodes


def test_concept_graph_top_concepts() -> None:
    builder = ConceptGraphBuilder()
    graph = builder.build(
        [
            _perceived("module_a", "alpha alpha alpha beta beta gamma"),
            _perceived("module_b", "alpha beta gamma delta"),
        ]
    )

    concepts = builder.top_concepts(graph, 3)

    assert len(concepts) == 3
    assert [node.frequency for node in concepts] == sorted(
        [node.frequency for node in concepts], reverse=True
    )


def test_bridge_detector_finds_shared() -> None:
    candidates = BridgeDetector().detect(_graph_with_shared_concepts())

    assert any(candidate.shared_concept_count > 0 for candidate in candidates)


def test_bridge_detector_no_self_pairs() -> None:
    candidates = BridgeDetector().detect(_graph_with_shared_concepts())

    assert all(candidate.module_a != candidate.module_b for candidate in candidates)


def test_bridge_detector_score_bounds() -> None:
    candidates = BridgeDetector().detect(_graph_with_shared_concepts())

    assert all(0.0 <= candidate.bridge_score <= 1.0 for candidate in candidates)


def test_bridge_detector_implicit_filter() -> None:
    graph = _graph_with_shared_concepts()
    coherence = CoherenceGraphDef(
        nodes=[
            NodeDef(node_id="module_a", description=""),
            NodeDef(node_id="module_b", description=""),
            NodeDef(node_id="module_c", description=""),
        ],
        edges=[EdgeDef(from_node="module_a", to_node="module_b", edge_type="feedback", weight=1.0)],
    )

    implicit = BridgeDetector(coherence).implicit_bridges(BridgeDetector().detect(graph))

    assert all({candidate.module_a, candidate.module_b} != {"module_a", "module_b"} for candidate in implicit)


def test_synthesis_fallback_no_llm(monkeypatch) -> None:
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    graph = _graph_with_shared_concepts()
    bridge = BridgeDetector().detect(graph)[0]

    result = BridgeSynthesizer().synthesize(bridge, graph)

    assert result.synthesis_text == (
        f"Modules '{bridge.module_a}' and '{bridge.module_b}' "
        f"share {bridge.shared_concept_count} concepts including: bridge, shared, signal."
    )


def test_synthesis_llm_available_flag(monkeypatch) -> None:
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    graph = _graph_with_shared_concepts()
    bridge = BridgeDetector().detect(graph)[0]

    result = BridgeSynthesizer().synthesize(bridge, graph)

    assert result.llm_available is False
