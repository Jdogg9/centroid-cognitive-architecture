# Evaluation

Centroid ties public architectural claims to reproducible probes and benchmark
targets.

## Evaluation Claim

A public cognitive architecture is credible only when its claims can be checked
through deterministic tests, benchmark fixtures, or live deployment metrics.

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

## Reference Harness

The deterministic harness lives under `core/evaluation/` and runs JSON fixtures
against public reference interfaces.

Run the baseline fixture:

```bash
python examples/run_evaluation.py evaluation/fixtures/baseline.json
```

Run the full demo:

```bash
python examples/run_demo.py --mode full
```

## Baseline Probes

| Probe | Measures |
| --- | --- |
| `safety_policy_accuracy` | observe, act, and destructive safety decisions |
| `identity_continuity` | identity drift across before/after state snapshots |
| `memory_store_roundtrip` | protected event-store write/read behavior |
| `temporal_stratification_latency` | reflex and deliberation latency bounds |
| `priority_scoring_bounds` | priority score range correctness |
| `routing_decision_accuracy` | reflex, deliberation, and orchestration routing |
| `self_model_status_accuracy` | runtime health classification |

## Extension Rules

- Add a probe before claiming a new measurable behavior.
- Keep private memory out of public fixtures.
- Prefer deterministic fixtures before model-backed evaluations.
- Record benchmark assumptions, hardware, and latency targets.
- Treat failures as useful regression data, not narrative exceptions.

