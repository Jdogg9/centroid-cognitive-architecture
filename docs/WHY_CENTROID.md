# Why Centroid?

Centroid is not positioned as a universal replacement for every agent
framework. It is a reference architecture for developers studying persistent
continuity, layered timing, safety-gated operation, and measurable agent state
over time.

## What It Emphasizes

| Area | Centroid focus |
| --- | --- |
| Continuity | Persistent state across sessions |
| Timing | Reflex, deliberation, and reconciliation loops |
| Safety | Approval-gated mutating actions |
| Identity | Versioned agent state and drift metrics |
| Evaluation | Deterministic probes and benchmarks |
| Configurability | Runtime behavior changes from schema-backed agent config |
| Reference UX | Runnable Holly examples |

## Comparison By Category

| Category | Common emphasis | Centroid emphasis |
| --- | --- | --- |
| Stateless LLM wrappers | One prompt-response exchange | Versioned continuity state and restoration |
| Workflow and agent orchestration frameworks | Tool chains, task graphs, integrations | Timing layers, approval gates, and evaluation probes around long-running state |
| Cognitive architectures | Structured models of cognition or production systems | Engineering contracts for persistent agent runtimes |
| Memory-augmented assistants | Retrieval and user-context recall | Provenance, drift checks, contradiction detection, and safety boundaries |

These categories can complement Centroid. A project can use an orchestration
framework or retrieval system behind Centroid's routing, memory, and safety
contracts.

## Holly's Role

Holly is the included reference agent that makes the architecture concrete.
She demonstrates configuration loading, persistent identity state, memory-backed
restoration, priority-weighted routing, temporal layering, and safety-gated
planning with synthetic deterministic data. `v0.3.0` extends that proof by
showing that a different config can produce different route, memory, and safety
outcomes without editing core runtime code.

Holly is not a private-origin persona and is not a claim of machine
consciousness or subjective experience.

## When Centroid Is A Good Fit

Centroid is most useful when you need to inspect or test:

- continuity across sessions
- memory provenance and restoration
- reflex versus deliberation timing
- approval gates for mutating actions
- identity drift or state drift
- reproducible agent behavior claims

For one-off stateless calls, a smaller wrapper may be enough. For production
tool orchestration, Centroid should be treated as the architecture around state,
timing, safety, and evaluation rather than as a replacement for all integration
libraries.
