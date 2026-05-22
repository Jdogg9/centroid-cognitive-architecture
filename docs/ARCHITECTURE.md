# Architecture

Centroid Cognitive Architecture separates a persistent agent into measurable
subsystems instead of treating a single model call as the full system.

## Layer Stack

1. Persistence: continuity state, journals, indexes, snapshots
2. Perception: screenshots, sensors, node telemetry, external signals
3. Reflex: low-latency checks, liveness, direct observations, emergency gates
4. Deliberation: slower planning, explanation, contradiction checks
5. Self-model: runtime health, goals, identity stability, state awareness
6. Coordination: routing between models, tools, nodes, and memory stores
7. Evaluation: drift, latency, correction timing, and consistency metrics

## Node Roles

CentroidOS is intended to run across heterogeneous nodes:

| Node role | Responsibility | Typical latency |
| --- | --- | --- |
| Reflex node | Health checks, direct observation, fast policy checks | milliseconds to seconds |
| Deliberation node | Planning, explanation, contradiction analysis | seconds to minutes |
| Memory node | Journaling, retrieval, compaction, provenance | seconds to minutes |
| Sensory node | Sensor capture and telemetry normalization | seconds |
| Orchestration node | Routing, approval gates, audit logs, shutdown | immediate to seconds |

## Message Contract

Every internal message should carry:

- `message_id`
- `timestamp`
- `source_node`
- `intent`
- `priority`
- `state_refs`
- `requires_approval`
- `audit_reason`

## Reference Flow

```text
sensory input
  -> reflex gate
  -> priority scoring
  -> router
  -> memory retrieval
  -> deliberation
  -> safety decision
  -> action or explanation
  -> audit log
  -> self-model update
```

## Design Rules

- Preserve operational continuity, not personal survival.
- Represent identity as state, policy, and history, not as metaphysical status.
- Keep private memory and privileged memory separated from public examples.
- Make every autonomous action reversible, auditable, or approval-gated.
- Treat self-modeling as internal state representation and consistency checking.

