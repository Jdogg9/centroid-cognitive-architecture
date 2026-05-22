# Memory Model

Centroid memory is a set of state stores with different privacy, latency, and
retention properties.

## Memory Classes

| Class | Purpose | Public equivalent |
| --- | --- | --- |
| Continuity state | Current runtime identity and health | Versioned state model |
| Event journal | Append-only operational history | Audit/event log |
| Working memory | Active task context | Session state |
| Long-term memory | Retrieved prior facts and summaries | Indexed archive |
| Privileged memory | Protected, high-significance records | Access-controlled state store |
| Sensory memory | Sensor and telemetry observations | Observation stream |

## Required Properties

- Append-only event history for critical runtime events
- Explicit provenance for retrieved facts
- Retention policy per memory class
- Redaction before public export
- Drift checks for identity and goal state
- Compaction that records what was summarized and why

## Non-Goals

Memory persistence is not proof of consciousness. It is an engineering mechanism
for continuity, reproducibility, and evaluation.

