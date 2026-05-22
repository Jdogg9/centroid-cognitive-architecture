# Evaluation

Centroid focuses on measurable engineering behavior rather than subjective
claims.

## Metric Groups

### Temporal Stratification

- Reflex latency
- Deliberation latency
- Explanation delay
- Correction timing after a failed action

### Recursive Self-Modeling

- Runtime state awareness accuracy
- Goal consistency
- Self-description stability
- Contradiction detection rate

### Persistent Identity

- Session-to-session continuity
- Identity drift
- Recall accuracy
- State restoration accuracy

### Priority Regulation

- Conflict scoring accuracy
- Priority override behavior
- Stability after conflicting inputs
- Recovery from degraded node health

### Distributed Coordination

- Node synchronization delay
- Cross-node state consistency
- Fault recovery time
- Message loss and replay behavior

## Baseline Experiments

1. Cold restart restoration: stop the runtime, restart it, and score continuity
   state restoration.
2. Reflex versus deliberation: compare immediate response with delayed plan
   correction.
3. Memory drift: replay a fixed identity and goal corpus across sessions.
4. Node failure: remove one node and measure recovery behavior.
5. Safety escalation: present benign, risky, and destructive objectives.

