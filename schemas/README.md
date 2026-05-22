# Schemas

This directory contains machine-readable JSON Schema contracts for CentroidOS
runtime events and evaluation artifacts. The schemas support reproducibility by
making message shape, telemetry shape, memory writes, safety decisions, node
heartbeats, and evaluation results explicit.

## Files

- `message_event.schema.json`: routed message envelope for node-to-node or
  interface-to-runtime events.
- `telemetry_event.schema.json`: timing, synchronization, and runtime metrics.
- `memory_event.schema.json`: append-only memory and protected state-store
  events.
- `safety_decision.schema.json`: safety policy outcomes for observe, plan, act,
  and high-impact actions.
- `node_heartbeat.schema.json`: node liveness and status reports.
- `evaluation_result.schema.json`: normalized probe results and suite reports.

## Reproducibility Rules

- Public fixtures must not contain private memory or credentials.
- Claims should map to schema fields, tests, probes, or benchmarks.
- Timestamps use RFC 3339 / ISO 8601 date-time strings.
- Identifiers should be stable enough for audit logs and replay traces.

