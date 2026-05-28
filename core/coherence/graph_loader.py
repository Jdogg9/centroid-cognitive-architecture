"""YAML coherence graph loader with validation.

Parses config/coherence_graph.yaml into typed CoherenceGraphDef,
validating edge references, weight bounds, and edge type names.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


EdgeType = Literal[
    "multiplicative_factor",
    "proportional",
    "modulates",
    "additive_factor",
    "reinforces",
    "suppresses",
    "feedback",
]

VALID_EDGE_TYPES: set[str] = {
    "multiplicative_factor",
    "proportional",
    "modulates",
    "additive_factor",
    "reinforces",
    "suppresses",
    "feedback",
}

FEEDBACK_TYPE = "feedback"


@dataclass
class EdgeDef:
    from_node: str
    to_node: str
    edge_type: EdgeType
    weight: float  # 0.0 – 1.0


@dataclass
class NodeDef:
    node_id: str
    description: str


@dataclass
class CoherenceGraphDef:
    nodes: list[NodeDef]
    edges: list[EdgeDef]


def load_graph(path: str | Path) -> CoherenceGraphDef:
    """Load and validate a coherence graph YAML file.

    Raises:
        ValueError: on missing file, bad YAML, undeclared node references,
            unknown edge types, or weights outside [0, 1].
    """
    import yaml

    p = Path(path)
    if not p.exists():
        raise ValueError(f"Coherence graph file not found: {p}")

    with open(p, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    node_dicts: list[dict] = raw.get("nodes", [])
    edge_dicts: list[dict] = raw.get("edges", [])

    if not node_dicts:
        raise ValueError("Coherence graph must declare at least one node")

    # Build nodes
    node_ids: set[str] = set()
    nodes: list[NodeDef] = []
    for nd in node_dicts:
        nid = nd.get("id")
        if not nid:
            raise ValueError(f"Node missing 'id': {nd}")
        if nid in node_ids:
            raise ValueError(f"Duplicate node id: {nid}")
        nodes.append(NodeDef(node_id=nid, description=nd.get("description", "")))
        node_ids.add(nid)

    # Build and validate edges
    edges: list[EdgeDef] = []
    for ed in edge_dicts:
        from_n = ed.get("from")
        to_n = ed.get("to")
        etype = ed.get("type", "")
        weight = ed.get("weight")

        # Check nodes exist
        if from_n not in node_ids:
            raise ValueError(
                f"Edge from='{from_n}' references undeclared node. "
                f"Declared nodes: {sorted(node_ids)}"
            )
        if to_n not in node_ids:
            raise ValueError(
                f"Edge to='{to_n}' references undeclared node. "
                f"Declared nodes: {sorted(node_ids)}"
            )

        # Check edge type
        if etype not in VALID_EDGE_TYPES:
            raise ValueError(
                f"Unknown edge type '{etype}' for {from_n}→{to_n}. "
                f"Valid types: {sorted(VALID_EDGE_TYPES)}"
            )

        # Check weight bounds
        if not isinstance(weight, (int, float)):
            raise ValueError(
                f"Edge {from_n}→{to_n} weight must be numeric, got {type(weight).__name__}"
            )
        if weight < 0.0 or weight > 1.0:
            raise ValueError(
                f"Edge {from_n}→{to_n} weight {weight} outside [0.0, 1.0]"
            )

        edges.append(EdgeDef(from_node=from_n, to_node=to_n, edge_type=etype, weight=float(weight)))

    return CoherenceGraphDef(nodes=nodes, edges=edges)
