# Memory Model

Centroid memory is a set of explicit state stores with different privacy,
latency, retention, and evaluation properties.

## Memory Claim

Persistent identity continuity can be studied only when memory writes, reads,
compaction, provenance, and drift are represented as measurable system events.

## Memory Classes

![Centroid memory flow](diagrams/memory_flow.svg)

| Class | Purpose | Public equivalent |
| --- | --- | --- |
| Continuity state | Current runtime identity and health | Versioned state model |
| Event journal | Append-only operational history | Audit/event log |
| Working memory | Active task context | Session state |
| Long-term memory | Retrieved prior facts and summaries | Indexed archive |
| Privileged memory | Protected high-significance records | Access-controlled state store |
| Sensory memory | Sensor and telemetry observations | Observation stream |

## Required Properties

- Append-only event history for critical runtime events
- Explicit provenance for retrieved facts
- Retention policy per memory class
- Redaction before public export
- Transparent memory policies
- Drift checks for identity and goal state
- Compaction records that explain what was summarized and why

## Measurable Claims

- memory recall consistency
- continuity state restoration accuracy
- identity drift
- contradiction rate across remembered state
- protected memory write/read round-trip correctness
- compaction loss rate

## Reference Probe

The baseline harness includes `memory_store_roundtrip`, which verifies that a
protected checkpoint can be written, retrieved, and checked without private
memory data.

Holly scenarios add public synthetic memory examples for project continuity,
support handoff continuity, operations telemetry, and identity checkpoints. The
`holly_project_state_restore` probe verifies that restored project events can
also expose a contradictory proposed change.

## Memory Event Example

```json
{
  "event_id": "memory-0001",
  "timestamp": "2026-01-01T00:00:00Z",
  "event_type": "protected_checkpoint",
  "content": "public demo continuity checkpoint",
  "source": "run_demo",
  "classification": "privileged",
  "provenance": "example fixture",
  "redacted": false,
  "metadata": {
    "public_demo": "true"
  }
}
```

Schema: [schemas/memory_event.schema.json](../schemas/memory_event.schema.json).

## Non-Goal

Memory persistence is not proof of consciousness, sentience, or subjective
experience. It is an engineering mechanism for continuity, reproducibility, and
evaluation.
