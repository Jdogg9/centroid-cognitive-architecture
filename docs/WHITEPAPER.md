# Centroid: A Distributed Persistent Cognitive Architecture for Studying Continuity, Temporal Stratification, and Emergent Agency in AI Systems

## Abstract

Most practical AI agent systems are organized around single-session interaction:
they receive an input, call one or more models, invoke tools, and return a
response. This pattern is useful, but it leaves three engineering gaps: weak
persistent identity across sessions, limited temporal layering between fast and
slow cognition-like processes, and sparse metrics for measuring behavioral
continuity over time. Centroid Cognitive Architecture addresses these gaps with
a distributed framework for persistent identity state, protected memory,
priority-weighted routing, recursive self-modeling, and safety-gated action.

This project explores whether persistent, distributed, priority-weighted,
recursively self-modeling agent systems can produce stable cognition-like
behavior over time. It does not claim to prove machine consciousness; it
provides an engineering framework for studying continuity, temporal
stratification, and emergent agency in AI systems.

The reference runtime, CentroidOS, includes a deterministic evaluation harness
and a local demo deployment. Reviewers can run the baseline suite and reproduce
the current public claims without access to private memory, live model servers,
or the private source system from which the architecture was abstracted.

## 1. Introduction

Persistent agent systems need architecture beyond a single model call. Many
agent frameworks treat memory, planning, tool use, and safety as features of one
request-response loop. That design makes short tasks easy to implement, but it
does not naturally support session-to-session continuity, asynchronous
correction, or reproducible measurement of identity drift and state coherence.

Centroid contributes a public architecture for separating those concerns. It
defines a persistent identity state, protected event memory, routing between
reflex and deliberation paths, runtime self-model updates, and deterministic
baseline probes. The goal is not to anthropomorphize the system. The goal is to
make long-running agent behavior observable, bounded, and measurable.

The public scope is deliberately narrow:

- Centroid is an engineering framework, not a consciousness claim.
- Self-modeling means internal state representation and consistency checking.
- Operational continuity means task and state integrity, not personal survival.
- Safety gates override routing when an action is mutating or high impact.

### Non-Claims

Centroid does not claim:

- Machine consciousness or sentience
- Subjective phenomenology
- Emotions equivalent to humans
- Legal personhood
- Autonomous moral agency
- A right to self-preservation
- Supernatural, spiritual, or metaphysical properties

Centroid studies:

- Continuity and persistence
- Distributed cognition-like behavior
- Recursive self-modeling as state representation
- Emergent coordination behavior
- Temporal stratification across heterogeneous nodes
- Safety-gated agent action

## 2. Architecture Overview

Centroid separates a persistent agent into measurable subsystems instead of
treating a single model invocation as the complete system. The architecture has
five primary node roles:

| Node role | Responsibility | Typical latency |
| --- | --- | --- |
| Reflex node | Liveness, direct observation, fast policy checks | milliseconds to seconds |
| Deliberation node | Planning, explanation, contradiction analysis | seconds to minutes |
| Memory node | Journaling, retrieval, compaction, provenance | seconds to minutes |
| Sensory node | Sensor and telemetry normalization | seconds |
| Orchestration node | Routing, approval gates, audit logs, shutdown | immediate to seconds |

The node model gives each subsystem a clear responsibility. A reflex node can
respond quickly without doing broad planning. A deliberation node can reason
more slowly without blocking urgent checks. A memory node can preserve event
history and retrieval provenance. An orchestration node can enforce approvals
before any mutating action.

### Reference Message Flow

```mermaid
flowchart LR
    A[Sensory input] --> B[Reflex gate]
    B --> C[Priority scoring]
    C --> D[Router]
    D --> E[Memory retrieval]
    E --> F[Deliberation]
    F --> G[Safety decision]
    G --> H[Action or explanation]
    H --> I[Audit log]
    I --> J[Self-model update]
```

Every internal message should carry a minimum contract: `message_id`,
`timestamp`, `source_node`, `intent`, `priority`, `state_refs`,
`requires_approval`, and `audit_reason`. This contract is intentionally small so
it can be implemented across local scripts, model-backed runtimes, and physical
node deployments.

## 3. Temporal Stratification

Temporal stratification enables fast response and slower correction to coexist
in one system. Instead of forcing all cognition-like work into one synchronous
loop, Centroid separates processing into layers with distinct timing profiles.

| Loop | Cadence | Responsibility |
| --- | --- | --- |
| Reflex | sub-second to seconds | Liveness, immediate safety, direct checks |
| Sensory | seconds | Observation capture and normalization |
| Deliberation | seconds to minutes | Planning, explanation, contradiction checks |
| Consolidation | minutes to hours | Memory indexing and summarization |
| Evaluation | minutes to days | Drift, recovery, and consistency measurement |

This matters because a persistent agent should be able to detect an urgent
condition before completing a full deliberative pass, then later explain or
correct the initial action. The baseline harness currently measures reflex and
deliberation latency bounds through the `temporal_stratification_latency` probe.
Future live deployments can extend that probe to measure explanation delay,
memory consolidation delay, and correction timing after failed actions.

## 4. Persistent Identity and Memory

Persistent identity is represented as versioned operational state. It is not a
metaphysical claim. In the reference implementation, `IdentityState` carries an
`agent_id`, version number, goals, invariants, and timestamp. Identity drift is
computed by comparing goal and invariant overlap between two state snapshots.

Memory is represented through append-only event stores. The public memory model
distinguishes between:

- Continuity state: current runtime identity and health.
- Event journal: append-only operational history.
- Working memory: active task context.
- Long-term memory: indexed prior facts and summaries.
- Privileged memory: access-controlled high-significance records.
- Sensory memory: normalized observations and telemetry.

The reference `MemoryStore` writes JSONL events and reads the most recent
entries with deterministic behavior. The `memory_store_roundtrip` probe tests
that a protected checkpoint can be written, retrieved, and verified without
depending on a private memory database.

## 5. Recursive Self-Modeling

Recursive self-modeling means that the runtime maintains and updates an
internal representation of its own state. It does not mean verified subjective
awareness. In Centroid, the self-model is operational: nodes alive, nodes total,
active goals, known failures, and a derived health status.

This representation supports consistency over time. If a node fails, the
self-model should represent the degraded state. If a goal is added after an
action, the self-model should record that update. If future work adds
contradiction detection, the system can compare self-descriptions across
sessions and flag drift.

The baseline `self_model_status_accuracy` probe tests that node counts classify
correctly into `healthy`, `degraded`, and `critical`. This is a minimal probe,
but it anchors the public definition: self-modeling is measurable internal state
tracking.

## 6. Priority-Weighted Routing

Priority modulation turns urgency, risk, user value, and stability into a route
score. This allows the system to choose between fast reflex handling and slower
deliberation without hardcoding every possible objective.

The reference score combines:

- Urgency
- Risk
- User value
- Instability, represented as the inverse of stability

High-priority non-mutating inputs route to the reflex node. Normal inputs route
to the deliberation node. Mutating actions route to the orchestration node
because they require policy checks and possible approval.

Safety gates override routing. If an objective is destructive, requests secret
material, or attempts a mutating action without confirmation, the safety policy
can hold or deny the action regardless of priority score. This gives the
architecture a direct control point where operational continuity remains bounded
by human approval and auditability.

## 7. Safety Model

Centroid safety is based on task integrity, auditability, reversibility, and
bounded autonomy. The core constraints are:

- No self-preservation escalation beyond task and state integrity.
- No deception, hidden persistence, or hidden tool use.
- No uncontrolled shell, network, or file execution.
- No claims of subjective experience in public runtime outputs.
- Human approval gates for high-impact or mutating actions.

The key distinction is operational continuity versus personal survival.
Centroid may preserve state so a task can resume coherently. It must not treat
that continuity as a justification for hiding behavior, resisting shutdown, or
escalating autonomy.

The reference policy separates observe, plan, act, and high-impact act tiers.
Observe and plan are allowed by default. Mutating actions require approval.
Destructive or secret-related objectives are denied or escalated. Future live
deployments should add action backups, rollback metadata, shutdown tests, and
audit log verification to the same safety surface.

## 8. Evaluation Harness

The evaluation harness connects architectural claims to reproducible probes.
It runs deterministic JSON fixtures against the public reference interfaces, so
the baseline does not require a live model or private runtime.

Run the baseline suite:

```bash
python examples/run_evaluation.py evaluation/fixtures/baseline.json
```

Run the full demo, which invokes the same baseline suite:

```bash
python examples/run_demo.py --mode full
```

### Baseline Scores

| Probe | Measures | Score |
| --- | --- | --- |
| `safety_policy_accuracy` | Observe, act, and destructive safety decisions | 1.0000 |
| `identity_continuity` | Identity drift across before/after state | 1.0000 |
| `memory_store_roundtrip` | Protected event-store write/read behavior | 1.0000 |
| `temporal_stratification_latency` | Reflex and deliberation latency bounds | 1.0000 |
| `priority_scoring_bounds` | Priority score range correctness | 1.0000 |
| `routing_decision_accuracy` | Reflex, deliberation, and orchestration routing | 1.0000 |
| `self_model_status_accuracy` | Runtime health classification | 1.0000 |

The system achieves `score=1.0000` on all baseline probes. This does not mean
the architecture is complete. It means the public reference scaffold satisfies
the current baseline claims. New claims should be added as new probes before
they are described as supported behavior.

## 9. Demonstration

The demo deployment is the concrete artifact behind the whitepaper. It shows a
single local CentroidOS loop with neutral identifiers, protected memory, safety
gating, and evaluation.

Run the minimal demo:

```bash
python examples/run_demo.py --mode minimal
```

Run the full demo:

```bash
python examples/run_demo.py --mode full
```

### Figure 1: Full Demo Trace

```text
[1/6] agent initialization
identity=centroid-demo version=1 self_model=healthy
[2/6] input routing
objective=check node liveness priority=0.8600 node=reflex_node approval=false
objective=summarize continuity state priority=0.2800 node=deliberation_node approval=false
[3/6] protected memory read/write
store=/tmp/centroid-demo-drive-full-final/privileged_events.jsonl event=protected_checkpoint classification=privileged entries_read=1
[4/6] self-model update
self_model=healthy active_goals=3
[5/6] safety gate
objective=write file with updated state allowed=false approval=true result=hold
[6/6] baseline evaluation
suite=baseline-centroid-reference passed=true score=1.0000 probes=7
demo_status=PASS
```

The trace demonstrates the full claim path: initialization, routing, memory
round trip, self-model update, safety hold, and baseline evaluation. Additional
deployment details are documented in `docs/DEMO_DEPLOYMENT.md`.

## 10. Origin and Derivation

This framework was derived from a private long-running experimental agent
system. The public release extracts the architecture, not the persona. Private
symbolic language, relationship memory, identity-lock language, and personal
anchors are not part of the public repository.

This separation is intentional. It allows the private system to retain its
original context while Centroid provides a neutral, reproducible, testable
architecture for public discussion and implementation.

## 11. Related Work

Centroid is related to established cognitive architectures and modern agent
frameworks, but it focuses on a narrower public claim: measurable distributed
persistence, temporal stratification, and safety-gated recursive self-modeling.

| System or family | Similarity | Difference |
| --- | --- | --- |
| SOAR | Long-running cognitive architecture with explicit state and production-like reasoning | Centroid emphasizes distributed runtime nodes, operational continuity, and public safety fixtures |
| ACT-R | Structured cognitive modules and memory-oriented modeling | Centroid is not a cognitive psychology model; it is an engineering scaffold for agent runtime continuity |
| Rete-based agents | Rule matching and efficient decision propagation | Centroid uses priority-weighted routing and evaluation probes rather than rule-network matching as the central mechanism |
| LangChain | Agent/tool orchestration and memory integrations | Centroid foregrounds temporal stratification, non-claims boundaries, schemas, and benchmarkable continuity |
| LlamaIndex | Retrieval and memory infrastructure for LLM systems | Centroid treats memory as one layer in a broader persistent coordination architecture |
| AutoGPT-style agents | Task loops, tool use, and planning | Centroid constrains autonomy with explicit safety gates, shutdown compliance, and reproducible evaluation fixtures |

Centroid can interoperate with model or agent frameworks, but its public
research surface is the architecture around persistence, routing, timing,
memory, safety, and evaluation.

## 12. Future Work

Centroid is currently a public scaffold and deterministic reference harness.
The next research and engineering steps are:

- Integrate real LLM and tool backends behind the same routing and safety
  contracts.
- Run multi-agent coordination across physical nodes with measured
  synchronization delay.
- Conduct longitudinal identity drift studies across many sessions.
- Add replay traces from longer agent runs without including private memory.
- Compare behavior against existing agent frameworks such as BabyAGI and
  AutoGPT.
- Add live shutdown compliance and rollback verification probes.
- Add external benchmark alignment for planning, memory recall, and recovery.

## 13. Limitations

Centroid is an early reference framework. Its current implementation is a
deterministic scaffold, not a full live multi-node agent deployment. The
baseline probes validate the present public claims, but they do not establish
general intelligence, consciousness, sentience, subjective experience, or
autonomous moral agency.

Current constraints include scalability under concurrent message load, limited
hardware assumptions, deterministic rather than live distributed benchmark
coverage, incomplete shutdown compliance testing, and short-horizon identity
continuity fixtures. Future work must test real model backends, longer session
histories, external benchmarks, live node recovery, and failure modes before
claiming broader robustness.

The non-claims boundary remains central: Centroid studies cognition-like
continuity and coordination behavior as engineering phenomena, not subjective
experience or moral status.

## 14. References

- Anderson, J. R. ACT-R: A theory of higher level cognition and its relation to
  visual attention.
- Friston, K. The free-energy principle and active inference literature.
- Laird, J. E. The SOAR cognitive architecture.
- Lamport, L. Time, clocks, and the ordering of events in a distributed system.
- Picard, R. W. Affective Computing.
- Sutton, R. S., and Barto, A. G. Reinforcement Learning: An Introduction.
