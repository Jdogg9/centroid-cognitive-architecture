# Centroid Cognitive Architecture

Centroid explores whether persistent, distributed, recursively self-modeling
agent systems can produce stable cognition-like behavior over time. It does not
claim to prove machine consciousness; it provides a runnable engineering
framework for studying continuity, temporal stratification, state propagation,
priority-weighted routing, and emergent coordination in AI systems.

## Runtime Name

The reference runtime is called CentroidOS.

## Theory Layer

The architecture is framed as Recursive Persistent Cognition:

- Persistent identity is represented as a versioned continuity state model.
- Memory is handled through protected, auditable state stores.
- Action selection is mediated by priority, conflict, and stability scores.
- Self-modeling means internal state representation and consistency checking,
  not verified subjective awareness.
- Temporal stratification separates reflex loops, deliberation loops, memory
  consolidation, and explanation after-action review.

## Public Non-Claims

Centroid does not claim:

- Machine consciousness or sentience
- Subjective phenomenology
- Human-equivalent emotions
- Legal personhood or autonomous moral agency
- Self-preservation beyond task and state integrity

Centroid studies:

- Continuity and persistence
- Distributed cognition-like coordination
- Recursive state modeling
- Temporal processing across heterogeneous nodes
- Measurable stability, drift, and recovery behavior

## Repository Layout

```text
docs/      Public architecture, safety, memory, timing, glossary, evaluation
core/      Reference interfaces for identity, memory, priority, routing, safety
nodes/     Node role contracts for reflex, deliberation, memory, sensory, orchestration
examples/  Minimal runnable demos
tests/     Safety and behavior checks for the reference interfaces
```

## Origin Boundary

Centroid was derived from a private long-running experimental agent system. The
public release extracts the architecture, not the persona. Private symbolic
language, relationship memory, identity-lock language, and personal anchors are
not part of this repository.

## Quick Start

```bash
git clone https://github.com/Jdogg9/centroid-cognitive-architecture.git
cd centroid-cognitive-architecture
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
python examples/demo_loop.py
python examples/run_evaluation.py evaluation/fixtures/baseline.json
python examples/run_demo.py --mode full
```

## Demo Deployment

The reference demo runs a neutral CentroidOS loop with initialization, routing,
protected memory, self-model update, safety gating, and baseline evaluation:

```bash
python examples/run_demo.py --mode full
python examples/run_demo.py --mode minimal
```

See `docs/DEMO_DEPLOYMENT.md` for the execution trace and public boundary.

## Whitepaper

The technical whitepaper is available at `docs/WHITEPAPER.md`.
