# Schemas

This directory contains machine-readable JSON Schema contracts for CentroidOS
runtime events and evaluation artifacts. The schemas support reproducibility by
making message shape, telemetry shape, memory writes, safety decisions, node
heartbeats, agent configuration, and evaluation results explicit.

## Files

- `message_event.schema.json`: routed message envelope for node-to-node or
  interface-to-runtime events.
- `telemetry_event.schema.json`: timing, synchronization, and runtime metrics.
- `memory_event.schema.json`: append-only memory and protected state-store
  events.
- `safety_decision.schema.json`: safety policy outcomes for observe, plan, act,
  and high-impact actions.
- `node_heartbeat.schema.json`: node liveness and status reports.
- `agent_config.schema.json`: bounded reference-agent configuration contract.
- `evaluation_result.schema.json`: normalized probe results and suite reports.

## Field Notes

### Message Event

- `message_id`: stable identifier for replay and audit.
- `timestamp`: event time in ISO 8601/RFC 3339 format.
- `source_node` and `target_node`: routing endpoints.
- `intent`: compact description of the requested operation.
- `priority`: normalized routing score from `0.0` to `1.0`.
- `state_refs`: references to state snapshots, memory entries, or trace IDs.
- `requires_approval`: whether a safety gate must approve the event.
- `audit_reason`: human-readable reason for recording the event.

### Telemetry Event

- `metric_name`: one of the supported measurable claim fields, such as
  `reflex_latency_ms`, `identity_drift`, or `node_sync_latency_ms`.
- `value` and `unit`: normalized metric payload.
- `labels`: optional dimensions for benchmark or deployment context.

### Memory Event

- `classification`: memory class such as `working`, `event_journal`,
  `long_term`, `privileged`, or `sensory`.
- `provenance`: source of the remembered content.
- `redacted`: whether content was redacted for public or lower-trust use.

### Safety Decision

- `mode`: observe, plan, act, or high-impact act.
- `allowed`: final policy decision.
- `requires_approval`: whether human approval is required.
- `rollback_path`: optional reference to reversal metadata.

### Node Heartbeat

- `node_role`: CentroidOS node role.
- `status`: health classification.
- `sequence`: monotonic heartbeat number.
- `capabilities`: declared runtime capabilities for coordination.

### Evaluation Result

- `suite_name`: evaluation suite identifier.
- `score`: normalized suite score.
- `results`: individual probe results.

## Examples

Valid examples live in `schemas/examples/`. Policy fixtures live in
`schemas/policy/`.

## Reproducibility Rules

- Public fixtures must not contain private memory or credentials.
- Claims should map to schema fields, tests, probes, or benchmarks.
- Timestamps use RFC 3339 / ISO 8601 date-time strings.
- Identifiers should be stable enough for audit logs and replay traces.
