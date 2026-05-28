# Centroid Cognitive Architecture: A Modular Framework for Persistent, Distributed, Recursively Self-Modeling Agents

## Abstract

Centroid Cognitive Architecture is an engineering framework for testing whether persistent, distributed, affect-weighted, recursively self-modeling agent systems can produce stable cognition-like behavior over time. The v0.7.0 implementation separates that problem into seven implemented layers: semantic memory, telemetry and self-modeling, module coherence, strategic forecast, twin world simulation, multimodal sensory encoding, and knowledge fusion. These layers do not attempt to prove or imply consciousness, sentience, subjective experience, or moral status. They provide explicit contracts for state continuity, append-only audit history, health measurement, counterfactual propagation, planning confidence, simulated divergence, and cross-module concept discovery. The implementation is intentionally stdlib-only where possible and grounded in deterministic tests rather than live-provider claims. At v0.7.0 the repository contains 174 pytest probes, including 29 baseline evaluation probes that still score 1.0000 through the deterministic harness.

## 1. Introduction

Most practical agent systems are still organized around a monolithic LLM-centric loop: receive input, build a prompt, call a model, optionally call tools, and return a response. That pattern is useful for short tasks, but it makes long-running behavior difficult to reason about. State is often implicit in prompts or external stores. Runtime health is rarely represented as a first-class object. Planning quality, memory provenance, and module coherence are usually evaluated after the fact, not as measured properties of the architecture. When such systems fail, the failure is hard to localize: the same model call may be responsible for perception, memory, planning, safety, and explanation.

Centroid takes a different approach. It treats cognition-like behavior as an engineering problem rather than a metaphysical question. The repository defines small modules with explicit contracts, deterministic tests, and neutral public terminology. Persistent behavior is modeled as versioned operational state. Memory is an append-only event stream plus retrieval indexes. Self-modeling is runtime health and state representation. Forecasting is calibrated prediction over plan threads. Simulation is a bounded fork of state used to estimate divergence before execution. Fusion is concept-level coordination between modules, with optional LLM synthesis treated as a non-authoritative presentation layer.

The scope of this paper is the implemented architecture in v0.7.0: what modules exist, what invariants they uphold, how they exchange state, and how the public claims are evaluated. It does not claim that the architecture is a complete live agent daemon. The current repository is a reference implementation with isolated module integration tests, runnable demos, deterministic fixtures, and a baseline evaluation harness. The next engineering step is to wire the seven layers into a continuous runtime loop while preserving the same contracts.

The practical motivation is operational. A long-running assistant, research agent, or automation worker needs to know what state it is preserving, which memories are evidence, which observations are stale, which module is unhealthy, and which proposed actions require human approval. Without those distinctions, "agent memory" becomes an undifferentiated prompt artifact and safety becomes a post-hoc filter. Centroid instead treats those concerns as separate state machines with measurable outputs. That separation lets a developer test memory search without invoking a planner, test anomaly detection without invoking a model provider, test safety preflight without executing an action, and test concept fusion without rewriting the coherence graph.

The framework also separates implementation claims from research hypotheses. The hypothesis is that persistent, distributed, affect-weighted, recursively self-modeling systems can produce stable cognition-like behavior. The implementation claim is narrower: this repository contains concrete modules, public contracts, and tests that measure continuity, retrieval, health, propagation, prediction, divergence, perception, and bridge detection. This paper therefore uses terms such as memory, self-model, affect weighting, and simulation in their engineering sense. Each term maps to files, schemas, tests, or output artifacts.

## 2. Design Principles

1. **Contracts before implementation.** Public behavior is anchored in schemas, typed dataclasses, config files, and deterministic probe names before prose claims are expanded.

   Implementation consequence: memory events, messages, safety decisions, telemetry events, provider configs, and evaluation results have explicit schema or type boundaries, while runtime audit records carry provenance such as config version and hash.

2. **Config-driven variation.** A persistent agent should be able to change policy and routing behavior without editing source code.

   Implementation consequence: YAML and JSON configuration drive coherence graph topology, agent routing thresholds, memory retention, provider selection, and safety outcomes; the same input can produce different bounded routes under different configs.

3. **Append-only event contract.** Operational history should be inspectable and resistant to accidental mutation.

   Implementation consequence: `MemoryStore` writes JSONL events, preserves the original append/tail API, and indexes events without rewriting the audit trail.

4. **Zero new dependencies.** The core release should remain reproducible on a fresh Python install.

   Implementation consequence: search, forecasting, simulation, sensory encoding, and fusion rely on the standard library and existing project utilities; optional provider paths are gated and not required for CI.

5. **Backward compatibility.** Public APIs should not break as new layers are added.

   Implementation consequence: tests preserve legacy self-model fields, planner step contracts, memory store behavior, packaged CLI resources, and baseline demo output while adding new modules.

6. **Non-claims boundary.** The framework measures behavior only; it does not assert subjective experience or moral status.

   Implementation consequence: public docs, tests, configs, and runtime output frame identity, continuity, affect weighting, and self-modeling as operational state and measurable consistency, not as proof of inner experience.

These principles are deliberately conservative. They make the repository easier to audit because every new capability must answer four questions: what file owns the behavior, what schema or type defines the contract, what artifact is written or returned, and what probe fails if the behavior regresses. That discipline is especially important for agent systems, where impressive demos can hide ambiguous state flow. Centroid favors boring interfaces over opaque orchestration: JSON, JSONL, YAML, dataclasses, deterministic tests, and explicit environment gates.

A second consequence is that optional intelligence remains optional. The architecture can call model providers or an Ollama-compatible local endpoint, but no baseline claim depends on doing so. The deterministic path is the reference path. Optional LLM synthesis in knowledge fusion is presentation; bridge detection itself is deterministic. Optional embeddings can accelerate semantic memory, but TF-IDF remains available and tested. This boundary keeps the architecture portable and reduces the chance that provider behavior is mistaken for architectural behavior.

## 3. Architecture Overview

Centroid v0.7.0 implements a seven-layer stack. The sensory layer normalizes code, telemetry, and arbitrary observations into `PerceivedText`. The memory layer stores append-only events and provides TF-IDF retrieval, provenance, and tiering. The planner layer forecasts short-, medium-, and long-horizon values and tracks plan threads. The self-model layer aggregates telemetry, scores health, writes world snapshots, and emits anomaly events. The safety layer gates action proposals and can be reinforced by simulation preflight. The coherence graph propagates module health through a YAML-defined directed graph and computes a scalar `CoherenceIndex(t)`. Knowledge fusion builds concept graphs over perceived text, detects implicit bridges, and can synthesize a readable bridge description.

```text
[Sensory Node] -> [Memory Store] -> [Planner]
                      |                |
                      v                v
               [Self Model]     [Safety Gate]
                      |                |
                      v                v
              [Coherence Graph] -> [Router]
                      |
                      v
              [Knowledge Fusion]
```

The diagram is intentionally logical rather than a claim of one always-on daemon. At v0.7.0, each layer is implemented and tested, and the demos exercise the baseline runtime. The full daemon loop remains future work.

The layers are meant to compose without collapsing into one large controller. A sensory scan can emit code perceptions into memory. Memory retrieval can inform forecasts. Telemetry can update the self-model and world snapshot. The coherence graph can read that snapshot and compute a system-level scalar. Simulation can fork the same snapshot and estimate risk. Fusion can inspect perceived modules and propose latent bridges. None of these steps requires granting a language model authority over state mutation. When a model is present, it is a bounded component behind adapter and safety contracts.

## 4. Core Modules

### 4.1 Semantic Memory (`core/memory/`)

**Purpose.** Semantic memory preserves operational events, retrieves relevant prior context, and assigns salience and provenance without requiring a database service.

**Key components.** `store.py` defines the append-only `MemoryStore`, `Event`, and search result contract. `tfidf_index.py` implements tokenization, term frequency, inverse document frequency, sparse cosine similarity, and ranked search. `retrieval.py` computes salience and provenance-weighted scores. `memory_pyramid.py` classifies indexed records into working, event-journal, long-term, privileged, and sensory tiers with deterministic compaction. `embedding_cache.py` provides an optional in-process embedding cache when an Ollama-compatible host is configured, but the default path remains TF-IDF.

**Key invariants.** The original append/tail API is preserved. Event writes are append-only JSONL. Classification values must match `memory_event.schema.json`. Compaction must not duplicate an entry as both retained and evicted. Retrieval must be deterministic in the default path.

**Measurable output.** The module produces ranked `SearchResult` records, tier counts, retained/evicted document IDs from compaction, and JSONL event history. Its probe surface includes memory schema validation, TF-IDF search, provenance tracking, salience scoring, tier classification, compaction, and backward compatibility.

### 4.2 Telemetry & Self-Model (`core/self_model/`)

**Purpose.** The self-model layer turns runtime observations into health scores, anomaly records, trends, and a reusable world snapshot.

**Key components.** `telemetry_aggregator.py` collects readings from registered sources while tolerating failing sources. `health_scorer.py` clips metric values, computes per-node and system health ratios, and reports trend direction. `anomaly_detector.py` uses a rolling baseline and Z-score thresholds to classify warnings and critical anomalies. `world_snapshot.py` writes `state/world_snapshot.json` and `state/world_trends.json` atomically. `model.py` preserves the public `SelfModelSnapshot` contract while adding tick behavior that can emit anomaly events.

**Key invariants.** Health values are clipped before averaging. Anomaly baselines exclude the current spike. Missing sources do not crash aggregation. Snapshot read of a missing file returns a safe empty result. Backward-compatible `status` and `health_ratio` behavior is preserved.

**Measurable output.** The layer produces node health maps, trend maps, system health ratio, anomaly count, optional `coherence_index`, and anomaly events appended to memory. These artifacts feed the coherence graph and simulation layers.

### 4.3 Module Coherence Graph (`core/coherence/`)

**Purpose.** The coherence graph represents causal influence between core modules and computes a scalar coherence signal over propagated health values.

**Key components.** `graph_loader.py` parses `config/coherence_graph.yaml` into typed node and edge definitions and validates references, edge types, and weight bounds. `propagation.py` applies non-feedback edges in Kahn topological order, then applies feedback edges in a bounded post-pass. `coherence_index.py` computes `CoherenceIndex(t)` and weakest/strongest module reports. `do_operator.py` implements a Pearl-style intervention by fixing a node value and severing inbound edges. `coherence_graph.py` orchestrates YAML load, snapshot read, propagation, index computation, snapshot writeback, config reload, and counterfactual simulation.

**Key invariants.** Edge references must point to declared nodes. Weights are bounded in `[0.0, 1.0]`. Unknown edge types fail validation. Propagated outputs are clamped. Feedback edges are excluded from topological sorting to prevent cycles from dominating forward propagation.

**Measurable output.** The module produces propagated node values, a `CoherenceReport`, optional snapshot writeback, and counterfactual deltas from `do(...)` interventions.

### 4.4 Strategic Forecast (`core/planner/`)

**Purpose.** The planner layer forecasts module state across multiple horizons and closes the loop between predictions and observed outcomes.

**Key components.** `forecast.py` implements exponential smoothing and generates short-, medium-, and long-horizon forecasts with confidence values. `calibration.py` tracks prediction error, signed bias, persistence, and round-trip loading from `state/calibration.json`. `plan_tree.py` manages plan thread lifecycle, including active, completed, and abandoned threads. `feedback_loop.py` registers forecast records, resolves them against observed outcomes, updates calibration, and adjusts confidence. `planner.py` preserves earlier plan and step contracts.

**Key invariants.** Forecast IDs are unique. Confidence starts conservatively under cold-start conditions. Repeated observations move predictions toward current values. Calibration updates incrementally and persists to disk. Plan threads cross clear lifecycle thresholds instead of silently disappearing.

**Measurable output.** The layer produces forecast records for three horizons, calibration records, plan tree state in `state/plan_tree.json`, delayed/active/completed thread views, and confidence updates after feedback resolution.

### 4.5 Twin World Simulation (`core/simulation/`)

**Purpose.** Twin simulation provides a bounded counterfactual workspace for estimating divergence and escalating risky actions before they execute.

**Key components.** `twin_buffer.py` forks world state from `state/world_snapshot.json` using deep-copy semantics and manages bounded twin buffers. `intervention.py` represents proposed state changes and applies them to forked snapshots. `divergence.py` computes recency-weighted divergence `D(t) = sum(lambda^(n-k) * d_k)` over differences between baseline and simulated trajectories. `safety_preflight.py` integrates divergence with the safety policy so an otherwise allowed action can be escalated to hold when simulated divergence exceeds threshold.

**Key invariants.** Forked state must not mutate the baseline snapshot. Divergence is bounded and recency-weighted. Safety preflight is conservative: it escalates allow to hold; it does not downgrade deny to allow. Simulation remains a pre-execution analysis layer, not a hidden execution channel.

**Measurable output.** The module produces twin snapshots, divergence scores, and preflight safety decisions that explain when `D(t)` crosses a threshold.

### 4.6 Multimodal Sensory Node (`nodes/sensory_node/`)

**Purpose.** The sensory node normalizes heterogeneous inputs into a shared textual latent space so code, telemetry, and observations can be compared.

**Key components.** `__init__.py` defines `PerceivedText` and exports the encoder and projector classes. `code_encoder.py` uses `ast.parse()` to extract Python module signatures, class and function first lines, docstrings, and comments without importing target modules. `telemetry_encoder.py` encodes health metrics with high/low qualifiers and reads `node_health` from world snapshots. `sensory_encoder.py` flattens arbitrary nested observations with dot-joined keys and caps content at 512 characters. `latent_projector.py` reuses the memory TF-IDF vector space for add, search, similarity, cross-modal search, and startup scanning.

**Key invariants.** Encoders return `PerceivedText` with source kinds `code`, `telemetry`, or `sensory`. Code scanning skips caches, Git metadata, and tests. Missing or non-Python files return `None`. Similarity requires both source IDs to be indexed and raises a source-specific `KeyError` otherwise. Startup scanning must not require a memory store.

**Measurable output.** The layer produces `PerceivedText` records, sorted search results, similarity scores, and optional memory events with `event_type="sensory_perception"`.

### 4.7 Knowledge Fusion (`core/fusion/`)

**Purpose.** Knowledge fusion finds concept-level relationships between modules that are not already explicit in the coherence graph.

**Key components.** `concept_graph.py` tokenizes `PerceivedText`, filters stopwords, removes single-module singletons, and builds concept-to-module and module-to-concept indexes. `bridge_detector.py` scans sorted module pairs, computes `bridge_score = shared_concept_count / min(len(set_a), len(set_b))`, and filters implicit bridges not covered by a direct coherence edge in either direction. `synthesis.py` creates deterministic fallback descriptions and optionally calls Ollama via `urllib.request` when configured.

**Key invariants.** Stopwords remain filtered. Concepts appearing in only one module and fewer than two times are excluded. Bridge pairs are unique and ordered. Optional LLM paths are gated by environment variables, use a five-second timeout, and fall back without raising when unavailable.

**Measurable output.** The layer produces `ConceptGraph` nodes, sorted top concepts, bridge candidates with scores in `[0.0, 1.0]`, implicit bridge lists, and `SynthesisResult` records that say whether an LLM was used.

Across all seven modules, the recurring pattern is the same: a narrow input contract, a deterministic transformation, a small output artifact, and a probe suite. This is not accidental. Persistent systems fail when state ownership is unclear. By forcing every layer to publish its artifact, Centroid makes cross-layer behavior inspectable. A failed forecast can be traced to calibration data. A degraded coherence score can be traced to propagated node health. A held action can be traced to safety policy or simulation divergence. A fusion bridge can be traced to shared concepts in `PerceivedText` rather than to an unexplained model summary.

The seven layers also make partial adoption possible. A project can use the memory store without the simulation layer, the sensory encoders without the planner, or the coherence graph without an LLM. The architecture is a reference stack, not an all-or-nothing product. That matters for reproducibility: each module can be evaluated independently before being wired into a larger daemon.

## 5. Safety Model

Centroid safety uses a three-tier decision policy: allow, hold, and deny. Allow covers read-only observation, deterministic analysis, and other non-mutating work that stays within policy. Hold covers operations that may be valid but require explicit approval, such as mutating actions, uncertain preconditions, or elevated divergence from simulation. Deny covers destructive actions, secret exposure, policy bypass attempts, and requests that violate the configured safety boundary.

The v0.7.0 simulation layer adds a safety preflight path. Before execution, a proposed intervention can be applied to a twin world fork. If the resulting recency-weighted divergence `D(t)` exceeds the configured threshold, preflight escalates an allow decision to hold. This is intentionally one-way. A simulation cannot make a denied action allowed; it can only add caution to an otherwise permissible action. The design treats divergence as a risk signal rather than a permission source.

The system explicitly does not implement autonomy escalation, hidden persistence, self-preservation beyond task and state integrity, uncontrolled tool execution, or claims of subjective experience. Model providers are not authoritative over Centroid state. Provider tool calls are normalized into proposals and remain subject to Centroid safety evaluation.

Human approval gates and audit logs are part of the contract. Mutating actions require confirmation or are held. Audit records preserve the reason for a route or safety disposition and redact sensitive values. This makes safety behavior reproducible in tests and inspectable in demos.

## 6. Evaluation

The evaluation strategy is deterministic by default. A deterministic probe harness matters because it lets reviewers reproduce public claims without live model access, private data, network providers, or timing-sensitive services. The baseline fixture exercises the original public architecture claims, while pytest modules exercise the v0.5.0 through v0.7.0 implementation layers.

Current probe count by module at v0.7.0:

| Module | Probes |
|---|---:|
| Baseline + installability | 29 |
| Memory search | 57 |
| Self-model telemetry | 24 |
| Coherence graph | 18 |
| Strategic forecast | 19 |
| Twin simulation | 16 |
| Sensory node | 15 |
| Knowledge fusion | 11 |
| **Total pytest probes** | **174** |

All 29 baseline evaluation probes still score `1.0000` at v0.7.0 through `examples/run_demo.py --mode full` and the baseline harness. The larger pytest suite verifies module contracts around memory, telemetry, coherence, forecasting, simulation, sensory encoding, fusion, demos, provider boundaries, schemas, safety, identity, and packaging.

The harness does not yet measure a single live daemon loop that runs all seven layers continuously. It also does not claim latency under production load, adversarial robustness, live provider quality, or multi-instance coordination. Those remain explicit future work.

The split between the baseline harness and pytest suite is intentional. The baseline harness is the public demonstration contract inherited from the original scaffold: it verifies safety, identity, memory round trips, temporal ordering, routing, self-model status, Holly scenarios, config-driven variation, and provider-adapter boundaries. The pytest suite is broader and closer to implementation: it verifies each new module directly. Future releases should reduce that split by promoting the most important pytest probes into harness fixtures so release summaries can cite one canonical system-level report.

## 7. Non-Claims

This framework does not claim:
- Machine consciousness or sentience
- Subjective phenomenological experience
- Emotions equivalent to human emotions
- Legal personhood or autonomous moral agency
- That any implemented behavior constitutes genuine understanding

This framework studies:
- Continuity and persistence in agent state
- Distributed cognition and temporal processing
- Recursive self-modeling and behavioral consistency
- Emergent coordination between independently correct modules

## 8. Future Work

1. **Live daemon loop.** The next milestone is wiring all seven modules into a single runtime cycle: sensory scan, memory update, self-model tick, coherence propagation, forecast update, simulation preflight, safety-gated routing, and fusion reporting. At v0.7.0 each module is implemented and integration-tested in isolation, but the repository does not yet claim a continuous live loop.

2. **Harness expansion.** The pytest probes for coherence, forecast calibration, anomaly detection, simulation divergence, sensory startup scanning, and fusion bridge detection should be promoted into the evaluation harness for system-level regression. That will make the baseline fixture represent more than the original 29 scaffold probes.

3. **Multi-agent coordination.** The coherence graph can be extended to span multiple Centroid instances. In that setting, implicit bridge detection becomes a coordination primitive: two instances with independently correct local modules could discover shared concepts and propose explicit graph edges or handoff contracts without requiring one central model to own all context.
