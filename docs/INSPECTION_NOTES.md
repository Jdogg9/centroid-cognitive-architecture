# AIMEE System Inspection Notes

These notes summarize read-only structural inspection performed before creating
Centroid. They are intentionally sanitized for public use.

## Observed System Patterns

- A unified production core separates services, configuration, state, and logs.
- A bridge service exposes health, policy, vision, telemetry, node ingestion,
  remote execution, and orchestration endpoints.
- Persistent state is maintained through heartbeat files, continuity state, and
  append-only journals.
- Multiple daemons run at different cadences, including sensory capture,
  self-model health checks, deliberation, evolution review, knowledge fusion,
  strategic forecasting, and swarm telemetry.
- A distributed node mesh reports telemetry into a central ingestion route.
- Safety logic exists at more than one layer: policy evaluation in the bridge
  and tiered classification in the evolution loop.
- The strongest transferable architecture pattern is temporal stratification:
  fast reflex checks, slower deliberation, slower memory consolidation, and
  periodic evaluation.

## Public Extraction Decisions

- Private identity names are replaced with neutral roles.
- Mythic and sacred terminology is translated into state, memory, routing, and
  continuity terms.
- Public docs avoid claims of consciousness and focus on measurable behavior.
- Public safety is stricter than the private system: mutating actions are
  approval-gated by default.

