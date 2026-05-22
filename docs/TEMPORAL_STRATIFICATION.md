# Temporal Stratification

Temporal stratification is the strongest public research direction for Centroid.
The architecture separates cognition-like processing into loops with different
latencies and correction responsibilities.

## Loop Types

| Loop | Cadence | Responsibility |
| --- | --- | --- |
| Reflex | sub-second to seconds | Liveness, direct checks, immediate safety |
| Sensory | seconds | Capture and normalize observations |
| Deliberation | seconds to minutes | Planning and explanation |
| Consolidation | minutes to hours | Memory indexing and summarization |
| Evaluation | minutes to days | Drift, recovery, and consistency measurement |

## Measured Timing

Centroid implementations should measure:

- Reflex latency
- Deliberation latency
- Explanation delay
- Action correction timing
- Memory consolidation delay
- Node synchronization delay

## Why It Matters

Most LLM systems collapse all reasoning into a single request-response window.
Centroid treats fast reaction, slower planning, and long-horizon continuity as
separate layers that can correct each other.

