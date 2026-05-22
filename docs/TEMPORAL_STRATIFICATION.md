# Temporal Stratification

Temporal stratification separates cognition-like processing into loops with
different latency, context, and correction responsibilities.

## Temporal Claim

A persistent agent can respond quickly while still allowing slower deliberation,
narrative reconciliation, and state correction to catch up.

![Centroid timing flow](diagrams/timing_flow.svg)

## Loop Types

| Loop | Cadence | Responsibility |
| --- | --- | --- |
| Reflex | sub-second to seconds | Liveness, direct checks, immediate safety |
| Sensory | seconds | Capture and normalize observations |
| Deliberation | seconds to minutes | Planning and explanation |
| Reconciliation | seconds to minutes | Align fast action with slower reasoning |
| Consolidation | minutes to hours | Memory indexing and summarization |
| Evaluation | minutes to days | Drift, recovery, and consistency measurement |

## Metrics

Centroid implementations should measure:

- reflex latency
- deliberation latency
- narrative reconciliation delay
- action correction timing
- memory consolidation delay
- node synchronization latency
- failover continuity

## Example Event

```json
{
  "event": "stimulus_detected",
  "reflex_response_ms": 31,
  "deliberative_response_ms": 4200,
  "state_reconciliation_ms": 4388
}
```

## Interpretation

Temporal stratification does not imply subjective experience. It is a systems
pattern for coordinating fast response, slower reasoning, state reconciliation,
and evaluation.
