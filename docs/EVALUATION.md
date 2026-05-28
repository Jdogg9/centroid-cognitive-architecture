# Evaluation

Centroid ties public architectural claims to reproducible probes and benchmark targets. The evaluation harness is deterministic: it validates system-level behavioral contracts against JSON fixtures and local reference interfaces. It is not a live-provider benchmark, live distributed-runtime measurement, or external adversarial robustness claim.

## Evaluation Claim

A public cognitive architecture is credible only when its claims can be checked through deterministic tests, benchmark fixtures, or explicitly scoped live deployment metrics.

## Quick Start

Run the original baseline behavior:

```bash
python3 examples/run_evaluation.py --mode full
```

Run a single expanded suite:

```bash
python3 examples/run_evaluation.py --mode full --suite coherence
```

Run the complete system-level harness gate:

```bash
python3 examples/run_evaluation.py --mode full --suite all
```

Expected complete harness result at v0.8.0 harness expansion: 68 probes, all passing at score 1.0000.

Installed CLI entry points can also use the packaged baseline fixture:

```bash
centroid-eval
```

Run implementation-level tests separately:

```bash
python3 -m pytest -q
```

Expected pytest result at v0.8.0 harness expansion: 174 passing probes.

## Harness Probe Suites

The deterministic harness lives under `core/evaluation/` and runs JSON fixtures under `evaluation/fixtures/` through the same `EvaluationHarness` runner. `baseline.json` remains unchanged; new module fixtures extend the existing harness instead of creating a parallel runner.

| Suite | Fixture | Probes | Covers |
| --- | --- | ---: | --- |
| `baseline` | `evaluation/fixtures/baseline.json` | 29 | Safety, continuity, timing, routing, memory roundtrip, Holly scenarios, config variation, and provider-boundary contracts |
| `memory` | `evaluation/fixtures/memory.json` | 6 | Append/tail compatibility, search, relevance ordering, tier assignment, compaction, and index rebuild |
| `self_model` | `evaluation/fixtures/self_model.json` | 6 | Health ratio bounds, status, snapshot writes, anomaly firing, fault-tolerant telemetry collection, and zero-source compatibility |
| `coherence` | `evaluation/fixtures/coherence.json` | 6 | YAML graph loading, clamped propagation, suppresses edges, scalar coherence bounds, tick writes, and simulate read-only behavior |
| `planner` | `evaluation/fixtures/planner.json` | 6 | Three-horizon forecasts, unique IDs, calibration updates/persistence, thread lifecycle, and feedback resolution |
| `simulation` | `evaluation/fixtures/simulation.json` | 5 | Isolated twin forks, dot-notation interventions, zero divergence, preflight escalation, and read-only preflight behavior |
| `sensory` | `evaluation/fixtures/sensory.json` | 5 | Code encoding, telemetry qualifiers, sensory truncation, self-similarity, and startup scan |
| `fusion` | `evaluation/fixtures/fusion.json` | 5 | Concept graph construction, stopword filtering, bridge detection, bridge score bounds, and no-LLM synthesis fallback |
| **Total** | `--suite all` | **68** | Complete deterministic system-level harness gate |

## Two-Layer Testing Model

Centroid now uses two required testing layers:

1. Harness probes (`python3 examples/run_evaluation.py --mode full --suite all`)
   - System-level behavioral contracts.
   - One representative probe per major invariant per module.
   - Fast, deterministic, and self-contained.
   - Fixture driven through `core/evaluation/`.
   - Produces a system-level score and pass/fail report.

2. Pytest probes (`python3 -m pytest -q`)
   - Implementation-level unit and integration contracts.
   - Broader coverage of edge cases, schema validation, and module internals.
   - Run in CI on push and pull request.

Both layers are required. CI verifies the pytest layer; the harness measures the system-level score that should be used as the complete deterministic regression gate before release.

## Metric Groups

### Temporal Stratification

- reflex latency
- deliberation latency
- narrative reconciliation delay
- action correction timing
- memory consolidation delay

### Persistent Identity Continuity

- memory recall consistency
- identity drift
- session continuity
- continuity state restoration accuracy
- contradiction rate

### Recursive Self-Modeling

- internal state reporting accuracy
- self-consistency
- planner-awareness alignment
- state-change awareness
- self-description stability

### Distributed Coordination

- node synchronization latency
- recovery time
- state propagation accuracy
- failover continuity
- cross-node consistency

### Priority-Weighted Regulation

- priority scoring bounds
- instability scoring
- valence-modulated routing
- stability-weighted planning
- safety override behavior

## Baseline Probe Scope

The baseline suite contains 29 deterministic probes over fixture data, synthetic Holly scenarios, config-driven runtime scenarios, and mock-provider/provider-boundary paths. It remains the default for `python3 examples/run_evaluation.py --mode full` to preserve existing behavior.

## Provider-Boundary Evaluation Scope

Mock provider mode is deterministic and is what CI verifies. Optional OpenAI, Anthropic, Ollama, and vLLM-style paths are opt-in provider adapter paths; live provider execution is not part of the deterministic baseline. Provider output is untrusted input. Provider tool proposals are safety-evaluated and audited by Centroid but remain non-executable.

## Extension Rules

- Add a probe before claiming a new measurable behavior.
- Keep private memory out of public fixtures.
- Prefer deterministic fixtures before model-backed evaluations.
- Keep harness probes self-contained; use temporary directories for state writes.
- Record benchmark assumptions, hardware, and latency targets for any live work.
- Treat failures as useful regression data, not narrative exceptions.
