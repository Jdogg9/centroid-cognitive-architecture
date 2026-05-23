# Copilot Instructions for Centroid Cognitive Architecture

## Build, test, and lint commands

Use the repo's editable install for local work:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Primary checks:

```bash
python -m pytest -q
python -m ruff check core examples tests benchmarks configs evaluation schemas templates
python -m black --check --workers 1 core examples tests benchmarks configs evaluation schemas templates
python -m build --wheel --no-isolation --outdir dist
```

Single-test examples:

```bash
python -m pytest tests/test_holly.py -q
python -m pytest tests/test_holly.py::test_project_companion_restores_state_and_detects_contradiction -q
```

Repo-specific runnable checks that matter when behavior changes:

```bash
python examples/run_evaluation.py evaluation/fixtures/baseline.json
centroid-eval
python examples/run_holly.py --scenario project-companion
centroid-agent --config templates/minimal_agent.json --scenario project-companion
python examples/run_config_comparison.py
python benchmarks/run_all.py
```

## High-level architecture

Centroid is a Python reference architecture for persistent agents; Holly is the bundled reference agent that exercises the architecture with deterministic synthetic scenarios. The code is organized so the reusable contracts live in `core/`, the public reference agent profiles live in `configs/holly/`, the runnable entry points live in `examples/`, the measurable claims live in `evaluation/fixtures/baseline.json`, and JSON schemas/examples live in `schemas/`.

The main runtime composition is easiest to understand from `core/runtime/` plus `examples/run_holly.py` and `examples/run_agent.py`: the runtime loads an `AgentConfig`, turns it into configured priority, safety, memory, and audit behavior, then runs the scenario through those policy-bearing components. That path is the clearest end-to-end reference for how identity, memory, routing, timing, safety, and config provenance are meant to work together.

Evaluation is a first-class architectural layer, not an afterthought. `core.evaluation.probes` encodes the measurable probes, `core.evaluation.cli` exposes them as the `centroid-eval` CLI, and `tests/test_holly.py` plus the domain-specific test folders verify both the core contracts and the Holly scenarios against deterministic fixtures. If you add a new public claim, scenario, or contract, update the fixture/schema/tests together.

`nodes/` documents the distributed node roles (`reflex_node`, `deliberation_node`, `memory_node`, `sensory_node`, `orchestration_node`), but most executable reference behavior in this repo is centralized in `core/` and `examples/` rather than a distributed runtime implementation.

## Key conventions

- Preserve the repo's non-claims boundary in code, docs, configs, and examples. Public language must stay operational and neutral: do not introduce consciousness, sentience, subjective experience, personhood, or self-preservation framing.
- Treat mutating behavior as approval-gated by default. In this codebase, observe/plan behavior is allowed, but mutating or risky actions route through orchestration and require explicit approval or denial with auditable reasons.
- Keep public examples deterministic and synthetic. Holly scenarios, evaluation fixtures, and benchmarks are meant to be reproducible reference probes, not live integrations or private-origin examples.
- Config-driven behavior matters here. `configs/holly/*.json` and `templates/minimal_agent.json` are part of the public contract; validate config changes against `schemas/agent_config.schema.json`, keep `agent_id` stable once fixtures depend on it, and preserve required invariants like approval gating, auditability, and no hidden tool effects.
- Memory is modeled as append-only JSONL events with explicit metadata/provenance. Public configs should continue to keep `retain_sensitive_data` false and `retain_provenance` true unless the repository intentionally expands that contract.
- When changing architecture-level behavior, tie it back to measurable coverage. This repository expects claims to be backed by tests, probes, benchmarks, or schemas rather than prose alone.
## v0.4.0 Provider Adapter Boundary

For v0.4.0 provider work, preserve deterministic mock behavior, avoid live network calls in CI, never add real credentials/private endpoints, and treat provider tool calls as Centroid-gated proposals only. MCP remains future v0.5.0 documentation and must not be implemented in this pass.
