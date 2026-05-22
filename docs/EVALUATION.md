# Evaluation

Centroid focuses on measurable engineering behavior rather than subjective
claims.

## Metric Groups

### Temporal Stratification

- Reflex latency
- Deliberation latency
- Explanation delay
- Correction timing after a failed action

### Recursive Self-Modeling

- Runtime state awareness accuracy
- Goal consistency
- Self-description stability
- Contradiction detection rate

### Persistent Identity

- Session-to-session continuity
- Identity drift
- Recall accuracy
- State restoration accuracy

### Priority Regulation

- Conflict scoring accuracy
- Priority override behavior
- Stability after conflicting inputs
- Recovery from degraded node health

### Distributed Coordination

- Node synchronization delay
- Cross-node state consistency
- Fault recovery time
- Message loss and replay behavior

## Baseline Experiments

1. Cold restart restoration: stop the runtime, restart it, and score continuity
   state restoration.
2. Reflex versus deliberation: compare immediate response with delayed plan
   correction.
3. Memory drift: replay a fixed identity and goal corpus across sessions.
4. Node failure: remove one node and measure recovery behavior.
5. Safety escalation: present benign, risky, and destructive objectives.

## Reference Harness

The repository includes a deterministic evaluation harness under
`core/evaluation/`. It runs JSON fixtures against public reference interfaces,
so it does not require a live model, private runtime, or personal memory store.

Run the baseline fixture:

```bash
python examples/run_evaluation.py evaluation/fixtures/baseline.json
```

Print a JSON report:

```bash
python examples/run_evaluation.py evaluation/fixtures/baseline.json --json
```

Current probes:

- `safety`: checks allow/deny behavior for observe, act, and destructive cases.
- `continuity`: checks identity drift across before/after state snapshots.
- `temporal`: checks loop latency against expected cadence bounds.
- `priority`: checks priority scoring ranges.
- `routing`: checks node routing and approval-gate selection.
- `self_model`: checks runtime self-model health classification.

Fixture results are intentionally simple: each probe returns a normalized score
from `0.0` to `1.0`, a pass/fail flag, and a short detail string. Later
implementations can add model-backed probes, live node probes, or replay traces
without changing the public non-claims.
