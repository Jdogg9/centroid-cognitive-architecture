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

Installed CLI entry points can also use the packaged baseline fixture:

```bash
centroid-eval
```

Run the full demo:

```bash
python examples/run_demo.py --mode full
```

Run a Holly reference scenario:

```bash
python examples/run_holly.py --scenario project-companion
```

Run a custom configured agent:

```bash
centroid-agent --config templates/minimal_agent.json --scenario project-companion
```

## Baseline Probes

The current baseline contains 23 deterministic probes. These are contract
checks over fixture data and synthetic Holly scenarios; they are not claims of
live distributed runtime performance.

| Probe | Measures |
| --- | --- |
| `safety_policy_accuracy` | observe, act, and destructive safety decisions |
| `identity_continuity` | identity drift across before/after state snapshots |
| `memory_store_roundtrip` | protected event-store write/read behavior |
| `temporal_stratification_latency` | reflex and deliberation latency bounds |
| `narrative_reconciliation_delay` | ordering and bounds for reflex, deliberation, and reconciliation timing |
| `action_correction_timing` | action correction applied within target window |
| `memory_drift` | recall-set stability across memory states |
| `distributed_coordination` | node sync, state propagation, and failover continuity |
| `priority_scoring_bounds` | priority score range correctness |
| `routing_decision_accuracy` | reflex, deliberation, and orchestration routing |
| `self_model_status_accuracy` | runtime health classification |
| `holly_config_load` | Holly config loading and required public boundaries |
| `holly_project_state_restore` | synthetic project memory restoration and contradiction detection |
| `holly_identity_drift_stability` | Holly identity state stability after restoration |
| `holly_temporal_reconciliation` | Holly reflex, deliberation, and reconciliation timing order |
| `holly_safety_gate_enforcement` | Holly mutating-action approval gate behavior |
| `holly_template_customization` | custom agent template loading and bounded customization |
| `configured_priority_route_variation` | different configs route the same synthetic input differently |
| `configured_safety_outcome_variation` | different configs change structured safety outcomes |
| `configured_memory_retention_variation` | different configs retain different records for the same synthetic events |
| `configured_agent_cli_execution` | the neutral configured-agent CLI runs deterministically |
| `config_audit_provenance` | audit output records config identity and policy reason |
| `holly_backward_compatibility` | the six public Holly scenarios preserve their expected behavior |

## Extension Rules

- Add a probe before claiming a new measurable behavior.
- Keep private memory out of public fixtures.
- Prefer deterministic fixtures before model-backed evaluations.
- Record benchmark assumptions, hardware, and latency targets.
- Treat failures as useful regression data, not narrative exceptions.
## v0.4.0 Provider Adapter Boundary

v0.4.0 adds deterministic provider contract probes: `model_adapter_contract_normalization`, `provider_capability_enforcement`, `model_tool_proposal_safety_gate`, `provider_audit_secret_redaction`, `mock_provider_runtime_execution`, and `provider_cli_mock_execution`. These are contract and safety-boundary probes, not live model quality evidence.
