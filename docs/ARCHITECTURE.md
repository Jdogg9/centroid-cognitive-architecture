# Architecture

Centroid Cognitive Architecture separates a persistent agent into measurable
subsystems instead of treating one model call as the entire system.

## Architectural Claim

Distributed persistent cognitive behavior becomes easier to reason about when
identity, memory, reflex response, deliberation, routing, safety, telemetry, and
evaluation are separated into explicit modules.

## Layer Stack

1. Persistence: continuity state, journals, indexes, snapshots
2. Perception: sensor input, task input, node telemetry
3. Reflex: low-latency checks, direct observations, immediate safety
4. Deliberation: slower planning, explanation, contradiction checks
5. Self-model: runtime health, goals, identity stability, state awareness
6. Coordination: routing between models, tools, nodes, and memory stores
7. Evaluation: drift, latency, recovery, consistency, and safety metrics

## Core Modules

| Module | Responsibility |
| --- | --- |
| `core/identity` | Persistent agent identity and identity drift scoring |
| `core/memory` | Append-only event memory and protected state stores |
| `core/affect` | Compatibility layer; public work should use priority terminology |
| `core/self_model` | Runtime self-model snapshots and health classification |
| `core/planner` | Plan and step contracts |
| `core/router` | Priority-based route selection and approval routing |
| `core/safety` | Safety policy decisions and denial/escalation behavior |
| `core/telemetry` | Planned metrics and observation normalization |
| `core/evaluation` | Deterministic probe runner and baseline reports |

## Node Roles

| Node role | Purpose | Typical latency |
| --- | --- | --- |
| Reflex node | Low-latency reaction and direct safety checks | milliseconds to seconds |
| Deliberation node | Long-form reasoning and narrative reconciliation | seconds to minutes |
| Memory node | Persistent storage, recall, compaction, provenance | seconds to minutes |
| Sensory node | Environment and task input normalization | seconds |
| Orchestration node | State coordination, permission gates, audit logs | immediate to seconds |

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
input
  -> reflex gate
  -> priority scoring
  -> router
  -> memory retrieval
  -> deliberation
  -> safety decision
  -> action or explanation
  -> audit log
  -> self-model update
  -> evaluation probe
```

## Diagram

![Centroid architecture flow](diagrams/architecture_flow.svg)

Mermaid source: [docs/diagrams/ARCHITECTURE_FLOW.md](diagrams/ARCHITECTURE_FLOW.md).

## Message Example

```json
{
  "message_id": "message-0001",
  "timestamp": "2026-01-01T00:00:00Z",
  "source_node": "sensory_node",
  "target_node": "router",
  "intent": "route_observation",
  "priority": 0.75,
  "state_refs": ["state:demo"],
  "requires_approval": false,
  "audit_reason": "demo routing event",
  "payload": {
    "observation": "node liveness check"
  }
}
```

Schema: [schemas/message_event.schema.json](../schemas/message_event.schema.json).

## Design Rules

- Preserve operational state continuity, not personal survival or autonomous
  self-interest.
- Represent identity as state, policy, goals, invariants, and history.
- Keep private-origin framing out of public examples.
- Make mutating actions approval-gated, auditable, and reversible where
  practical.
- Treat recursive self-modeling as internal state representation and consistency
  checking.
- Tie every public architectural claim to an evaluation or benchmark target.
