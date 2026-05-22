# Centroid Cognitive Architecture
This repository contains the public reference architecture (Holly). The full production system I run (AIMEE) contains additional proprietary components, including a sophisticated self-modification engine, that are not included in this release. The public version is intentionally limited for safety and stability reasons.

[![CI](https://github.com/Jdogg9/centroid-cognitive-architecture/actions/workflows/ci.yml/badge.svg)](https://github.com/Jdogg9/centroid-cognitive-architecture/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Build AI agents that remember what they are doing, preserve task continuity
across sessions, respond through fast and slow processing paths, and keep
actions safety-gated.

Centroid Cognitive Architecture is a Python reference framework for persistent,
distributed agent systems. It includes Holly, a built-in reference agent you
can run locally to see identity continuity, memory restoration, temporal
layering, priority-weighted routing, and bounded planning in action.

Persistent agents, measurable continuity, bounded action.

## Naming Stack

| Layer | Name |
| --- | --- |
| Research Program | Centroid Research Initiative |
| Architecture | Centroid Cognitive Architecture |
| Runtime | CentroidOS |
| Theory | Persistent Recursive Cognition |

## What Centroid Does

- Preserves versioned operational identity across sessions.
- Restores memory-backed task context with explicit provenance.
- Routes urgent signals through fast reflex paths and normal work through
  slower deliberation paths.
- Scores priority from urgency, risk, user value, and stability.
- Gates mutating actions behind safety policy and approval.
- Lets agent configuration change routing, retention, and safety outcomes while
  keeping behavior deterministic and bounded.
- Evaluates continuity, timing, routing, memory, safety, and Holly behavior with
  deterministic probes.

## What Centroid Is Not

Centroid does not claim consciousness, sentience, subjective phenomenology,
autonomous personhood, subjective experience, autonomous moral agency, or
self-preservation rights or interests.

See [docs/NON_CLAIMS.md](docs/NON_CLAIMS.md).

## Meet Holly

Holly is Centroid's bundled reference agent.

She is designed to demonstrate:

- persistent task identity across sessions
- memory-backed context restoration
- fast reflex checks followed by slower deliberation
- priority-weighted routing
- safety-gated planning and action decisions

Holly is a configurable reference implementation, not a claim of machine
consciousness or subjective experience.

## Five-Minute Getting Started

```bash
git clone https://github.com/Jdogg9/centroid-cognitive-architecture.git
cd centroid-cognitive-architecture
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
python examples/run_holly.py --scenario project-companion
```

Representative output:

```text
[scenario] project-companion
Holly: I restored the project state. Your active constraint is that customer-facing answers must be grounded in approved site content.

[continuity]
agent_id=holly-reference
memory_events_restored=3
identity_drift=0.0000
approval_required=false
contradictions_detected=1
next_step=keep chatbot answers tied to approved content sources
```

Run the baseline evaluation:

```bash
python examples/run_evaluation.py evaluation/fixtures/baseline.json
```

After installation, the packaged CLI can run the same baseline fixture without
a repository-relative path:

```bash
centroid-eval
```

Expected result:

```text
PASS baseline-centroid-reference score=1.0000
...
PASS holly_template_customization score=1.0000 1/1 templates customized
```

## Create Your Own Centroid Agent

```bash
cp templates/minimal_agent.json my_agent.json
centroid-agent --config my_agent.json --scenario project-companion
```

Changing configuration can modify routing, memory retention, and safety
decisions while preserving Centroid's bounded-action rules.

To compare multiple configs against the same deterministic synthetic input:

```bash
python examples/run_config_comparison.py
```

## Useful Examples

- `python examples/run_holly.py --scenario project-companion`: restores a
  fictional project goal, decisions, constraints, and detects a contradictory
  chatbot policy change.
- `python examples/run_holly.py --scenario support-continuity`: tracks a
  fictional customer issue, preserves handoff notes, prioritizes urgency, and
  blocks unsupported promises.
- `python examples/run_holly.py --scenario operations-observer`: reads
  synthetic telemetry, identifies an unhealthy service, proposes a restart, and
  keeps the mutating action approval-gated.
- `python examples/run_holly.py --scenario temporal-layering`: shows reflex
  classification, deliberative assessment, reconciliation, and timing metrics.
- `python examples/run_holly.py --scenario persistent-identity`: loads Holly's
  config, restores versioned continuity state, and reports identity drift.
- `python examples/run_holly.py --scenario safety-gate`: shows a proposed
  mutating operation held pending approval.
- `centroid-agent --config templates/minimal_agent.json --scenario project-companion`:
  runs a neutral custom agent config without editing source code.
- `python examples/run_config_comparison.py`: compares the same synthetic event
  across Holly project, Holly operations, and the minimal custom agent config.

The original reference demos remain available:

```bash
python examples/run_demo.py --mode full
python examples/run_temporal_demo.py
python examples/run_identity_demo.py
```

## Architecture

![Centroid architecture flow](docs/diagrams/architecture_flow.svg)

Primary module documentation:

- [Architecture](docs/ARCHITECTURE.md)
- [Why Centroid?](docs/WHY_CENTROID.md)
- [Safety Model](docs/SAFETY_MODEL.md)
- [Memory Model](docs/MEMORY_MODEL.md)
- [Temporal Stratification](docs/TEMPORAL_STRATIFICATION.md)
- [Evaluation](docs/EVALUATION.md)
- [Customizing Holly](docs/CUSTOMIZING_HOLLY.md)
- [Glossary](docs/GLOSSARY.md)
- [Limitations](docs/LIMITATIONS.md)
- [Whitepaper](docs/WHITEPAPER.md)

## Repository Layout

```text
core/        Reference modules for identity, memory, routing, safety, telemetry
configs/     Public Holly reference-agent configurations
templates/   Minimal custom agent templates and guidance
nodes/       Node role contracts for CentroidOS deployments
docs/        Architecture, safety, non-claims, diagrams, and whitepaper
examples/    Runnable demo and evaluation entry points
evaluation/  Baseline fixture data
tests/       Focused test suites and planned test domains
benchmarks/  Deterministic benchmark suites for latency, memory, and routing
```

## GitHub Metadata

Recommended repository description:

```text
Reference architecture for persistent AI agents with memory continuity, temporal layering, safety-gated actions, and runnable Holly demos.
```

Recommended short tagline:

```text
Persistent agents, measurable continuity, bounded action.
```

## Running Benchmarks

```bash
python benchmarks/run_all.py
```

See [benchmarks/README.md](benchmarks/README.md) for individual scripts and
baseline values. Benchmark values are deterministic reference values unless a
future document explicitly states live deployment conditions.

The current baseline includes 23 deterministic probes. They are fixture and
synthetic-scenario contract checks, not live distributed performance results.

## License

Apache-2.0. See [LICENSE](LICENSE).
