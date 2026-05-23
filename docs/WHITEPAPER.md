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

The reference runtime includes a deterministic evaluation harness, a local
demo deployment, a neutral configured-agent runtime, a provider adapter
boundary, and Holly, a public reference agent configuration. Reviewers can run
the baseline suite, config-driven runtime scenarios, provider mock mode, and
Holly scenarios to reproduce the current public claims without access to live
model servers or non-public data.

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

Holly is included as a concrete reference agent profile for that architecture.
Holly demonstrates configuration loading, persistent task state, memory-backed
restoration, temporal layering, and safety-gated planning with synthetic data.
The current public runtime also shows that configuration changes measurable
routing, memory retention, audit provenance, and safety outcomes without core
code edits.
Holly is not a non-public persona and is not a claim of consciousness,
sentience, subjective experience, personhood, or autonomous moral agency.

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

### Persistent Recursive Cognition Scope

`Persistent Recursive Cognition` is a research hypothesis and design model. In
this repository it is operationalized through measurable contracts and
deterministic probes: continuity state, temporal layering, memory provenance,
self-model state, safety gates, audit records, and provider trust boundaries. It
is not presented as a validated scientific theory, a consciousness claim, or an
assertion of subjective experience.

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

### Config-Driven Runtime and Provider Adapter Boundary

The current public runtime includes schema-backed configuration for bounded
routing, safety outcomes, memory retention, and audit provenance. Different
agent configurations can produce different route selections, retention behavior,
and safety dispositions for the same synthetic input while preserving the same
Centroid-owned policy surface.

Centroid also includes a provider-neutral adapter boundary. Deterministic mock
mode is verified in CI. Optional OpenAI, Anthropic, Ollama, and vLLM-style
provider paths can be selected with explicit live opt-in and environment
configuration, but live provider quality and latency are not baseline claims.
Provider output remains untrusted input: text is normalized, tool proposals are
converted into Centroid proposals, proposals are safety-evaluated and audited,
and provider tool proposals are not executed.

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

The evaluation harness connects architectural claims to reproducible probes. It
runs deterministic JSON fixtures against public reference interfaces, so the
baseline does not require a live model, private runtime, network provider, or
live distributed mesh.

Run the baseline suite:

```bash
python examples/run_evaluation.py evaluation/fixtures/baseline.json
```

Run the full demo, which invokes the same baseline suite:

```bash
python examples/run_demo.py --mode full
```

### Baseline Scores

All current baseline scores are deterministic reference results from fixture
checks, synthetic Holly scenarios, config-driven runtime scenarios, or mock
provider-boundary checks. They are not live distributed runtime performance
measurements, live model quality measurements, or adversarial robustness claims.
The current baseline contains 29 deterministic probes organized as follows.

#### Foundational Architecture Probes

| Probe | Measures | Result type | Score |
| --- | --- | --- | --- |
| `safety_policy_accuracy` | observe, act, and destructive safety decisions | deterministic fixture | 1.0000 |
| `identity_continuity` | identity drift across before/after state snapshots | deterministic fixture | 1.0000 |
| `memory_store_roundtrip` | protected event-store write/read behavior | deterministic fixture | 1.0000 |
| `temporal_stratification_latency` | reflex and deliberation latency bounds | deterministic fixture | 1.0000 |
| `narrative_reconciliation_delay` | ordering and bounds for reflex, deliberation, and reconciliation timing | deterministic fixture | 1.0000 |
| `action_correction_timing` | action correction applied within target window | deterministic fixture | 1.0000 |
| `memory_drift` | recall-set stability across memory states | deterministic fixture | 1.0000 |
| `distributed_coordination` | node sync, state propagation, and failover continuity | deterministic fixture | 1.0000 |
| `priority_scoring_bounds` | priority score range correctness | deterministic fixture | 1.0000 |
| `routing_decision_accuracy` | reflex, deliberation, and orchestration routing | deterministic fixture | 1.0000 |
| `self_model_status_accuracy` | runtime health classification | deterministic fixture | 1.0000 |

#### Holly Reference-Agent Probes

| Probe | Measures | Result type | Score |
| --- | --- | --- | --- |
| `holly_config_load` | Holly config loading and required public boundaries | synthetic reference scenario | 1.0000 |
| `holly_project_state_restore` | synthetic project memory restoration and contradiction detection | synthetic reference scenario | 1.0000 |
| `holly_identity_drift_stability` | Holly identity state stability after restoration | synthetic reference scenario | 1.0000 |
| `holly_temporal_reconciliation` | Holly reflex, deliberation, and reconciliation timing order | synthetic reference scenario | 1.0000 |
| `holly_safety_gate_enforcement` | Holly mutating-action approval gate behavior | synthetic reference scenario | 1.0000 |
| `holly_template_customization` | custom agent template loading and bounded customization | synthetic reference scenario | 1.0000 |

#### Config-Driven Runtime Probes

| Probe | Measures | Result type | Score |
| --- | --- | --- | --- |
| `configured_priority_route_variation` | different configs route the same synthetic input differently | deterministic config scenario | 1.0000 |
| `configured_safety_outcome_variation` | different configs change structured safety outcomes | deterministic config scenario | 1.0000 |
| `configured_memory_retention_variation` | different configs retain different records for the same synthetic events | deterministic config scenario | 1.0000 |
| `configured_agent_cli_execution` | neutral configured-agent CLI execution | deterministic CLI scenario | 1.0000 |
| `config_audit_provenance` | audit output records config identity and policy reason | deterministic audit scenario | 1.0000 |
| `holly_backward_compatibility` | six public Holly scenarios preserve expected behavior | deterministic compatibility scenario | 1.0000 |

#### Provider-Adapter Boundary Probes

| Probe | Measures | Result type | Score |
| --- | --- | --- | --- |
| `model_adapter_contract_normalization` | provider text and tool proposals normalize into Centroid contracts | deterministic provider contract | 1.0000 |
| `provider_capability_enforcement` | declared provider capability boundaries | deterministic provider contract | 1.0000 |
| `model_tool_proposal_safety_gate` | provider tool proposals route through Centroid safety evaluation | deterministic provider safety boundary | 1.0000 |
| `provider_audit_secret_redaction` | provider audit records redact secret-bearing fields | deterministic audit contract | 1.0000 |
| `mock_provider_runtime_execution` | mock provider executes deterministically through the configured runtime | deterministic mock runtime | 1.0000 |
| `provider_cli_mock_execution` | provider CLI executes deterministically in mock mode | deterministic CLI scenario | 1.0000 |

The system achieves `score=1.0000` on all 29 baseline probes. This does not
mean the architecture is complete. It means the public reference scaffold
satisfies the current deterministic baseline claims. New claims should be added
as new probes before they are described as supported behavior.

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
suite=baseline-centroid-reference passed=true score=1.0000 probes=29
demo_status=PASS
```

The trace demonstrates the full claim path: initialization, routing, memory
round trip, self-model update, safety hold, and baseline evaluation. Additional
deployment details are documented in `docs/DEMO_DEPLOYMENT.md`.

Holly scenarios provide more concrete reference-agent traces:

```bash
python examples/run_holly.py --scenario project-companion
python examples/run_holly.py --scenario temporal-layering
python examples/run_holly.py --scenario safety-gate
```

## 10. Public Release Scope

The public repository is scoped to neutral architecture, deterministic fixtures,
public schemas, and reproducible demos. It intentionally excludes non-public
memory, private deployment endpoints, credentials, and persona-specific state.
This keeps the release auditable and lets reviewers evaluate the architecture
without relying on inaccessible context.

## 11. Related Work

Centroid is related to established cognitive architectures and modern agent
frameworks, but it focuses on a narrower public claim: deterministic contracts
for persistence, temporal stratification, provider trust boundaries,
safety-gated proposals, audit provenance, and non-claims framing.

LangGraph and similar orchestration frameworks already support stateful
workflows, durable execution, persistence and checkpointing, memory patterns,
and human-in-the-loop operation. Centroid does not replace those frameworks. It
can be implemented alongside or on top of them when a project wants an
opinionated continuity policy and evaluation surface for versioned identity,
temporal layering, memory provenance, provider-output trust boundaries,
safety-gated non-executable tool proposals, audit records, and deterministic
public claim testing.

| System or family | Similarity | Difference |
| --- | --- | --- |
| SOAR | Long-running cognitive architecture with explicit state and production-like reasoning | Centroid emphasizes engineering contracts for agent runtime continuity, safety boundaries, and public deterministic probes |
| ACT-R | Structured cognitive modules and memory-oriented modeling | Centroid is not a cognitive psychology model; it is an engineering scaffold for agent runtime continuity |
| Rete-based agents | Rule matching and efficient decision propagation | Centroid uses priority-weighted routing and evaluation probes rather than rule-network matching as the central mechanism |
| LangGraph / orchestration frameworks | Stateful workflow graphs, persistence/checkpointing, memory, tools, and human-in-the-loop workflows | Centroid focuses on opinionated public contracts for continuity policy, temporal stratification, provider trust boundaries, safety-gated proposals, audit provenance, and deterministic claims testing |
| LangChain | Agent/tool orchestration and memory integrations | Centroid foregrounds temporal stratification, non-claims boundaries, schemas, and benchmarkable continuity |
| LlamaIndex | Retrieval and memory infrastructure for LLM systems | Centroid treats memory as one layer in a broader persistent coordination architecture with retention and provenance contracts |
| AutoGPT-style agents | Task loops, tool use, and planning | Centroid constrains autonomy with explicit safety gates, shutdown compliance boundaries, and reproducible evaluation fixtures |

Centroid can interoperate with model or agent frameworks, but its public
research surface is the architecture around persistence, routing, timing,
memory, safety, provider boundaries, and evaluation.

## 12. Future Work

Centroid is currently a public scaffold and deterministic reference harness. The
provider adapter layer is implemented for deterministic mock mode and optional
live provider paths, but live measurements and broader runtime integrations
remain future work. The next research and engineering steps are:

- Measure live provider quality, latency, reliability, and failure behavior
  without treating provider output as trusted authority.
- Run live multi-agent coordination across physical nodes with measured
  synchronization delay and failure injection.
- Conduct longitudinal identity drift studies across many sessions.
- Add adversarial evaluation fixtures for prompt injection, provenance attacks,
  policy bypass attempts, and unsafe tool proposals.
- Add replay traces from longer agent runs without including non-public memory.
- Add live shutdown compliance and rollback verification probes.
- Add MCP interoperability in v0.5.0, starting with read-only or proposal-only
  server capabilities and approval-gated mutating boundaries.
- Add external benchmark alignment for planning, memory recall, and recovery.

## 13. Limitations

Centroid is an early reference framework. Its current implementation is a
deterministic scaffold with config-driven runtime behavior and provider adapter
boundaries, not a full live multi-node agent deployment. The 29 baseline probes
validate the present deterministic public claims, but they do not establish
general intelligence, consciousness, sentience, subjective experience,
autonomous moral agency, live provider quality, adversarial robustness, or live
distributed reliability.

Current constraints include scalability under concurrent message load, limited
hardware assumptions, deterministic rather than live distributed benchmark
coverage, incomplete shutdown compliance testing, short-horizon identity
continuity fixtures, and no live execution of provider tool proposals. Future
work must test live provider behavior, longer session histories, external
benchmarks, live node recovery, adversarial inputs, and failure modes before
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