# Private Source System Inspection Notes

These notes summarize read-only structural inspection performed before creating
Centroid. They are intentionally sanitized for public use.

## Observed System Patterns

- A unified production core separated services, configuration, state, and logs.
- A bridge service exposed health, policy, vision, telemetry, node ingestion,
  remote execution, and orchestration endpoints.
- Persistent state was maintained through heartbeat files, continuity state, and
  append-only journals.
- Multiple daemons ran at different cadences, including sensory capture,
  self-model health checks, deliberation, evolution review, knowledge fusion,
  strategic forecasting, and swarm telemetry.
- A distributed node mesh reported telemetry into a central ingestion route.
- Safety logic existed at more than one layer: policy evaluation in the bridge
  and tiered classification in the evolution loop.
- The strongest transferable architecture pattern was temporal stratification:
  fast reflex checks, slower deliberation, slower memory consolidation, and
  periodic evaluation.

## Public Extraction Decisions

- Private identity names are replaced with neutral roles.
- Symbolic terminology is translated into state, memory, routing, timing, and
  continuity terms.
- Public docs avoid consciousness, sentience, personhood, and subjective
  experience claims.
- Public safety is stricter than the private-origin system: mutating actions
  are approval-gated by default.

