## Centroid Cognitive Architecture v0.7.0

Full implementation of the seven-layer cognitive architecture. All modules
are stdlib-only, zero external dependencies, 174 probes passing.

### New in v0.7.0 (Phase 3)

**Twin World Simulation** (`core/simulation/`)
- State forking via deep-copy of `world_snapshot.json`
- Recency-weighted divergence metric `D(t) = Σ λ^(n−k) × d_k`
- Safety preflight integration: allow → hold escalation when `D(t)` exceeds threshold
- 16 probes

**Multimodal Sensory Node** (`nodes/sensory_node/`)
- AST-based code encoder (signatures, docstrings, comments)
- Telemetry encoder with high/low qualifiers
- Nested observation flattener with 512-char truncation
- Shared TF-IDF latent space for cross-modal similarity
- Startup scan of `core/` emits `sensory_perception` events to `MemoryStore`
- 15 probes

**Knowledge Fusion** (`core/fusion/`)
- Concept graph built from `PerceivedText` corpus
- Implicit bridge detection: concept pairs spanning modules with no DAG edge
- Optional LLM synthesis via Ollama (`CENTROID_OLLAMA_MODEL`, default `phi4-mini:latest`)
- Deterministic fallback when LLM unavailable
- 11 probes

**Packaging**
- `pyproject.toml`: PEP 621 license table, version 0.7.0
- Legacy private Ollama environment fallback renamed to `CENTROID_OLLAMA_URL`

### Previously completed

- v0.6.0: Module Coherence Graph + Strategic Forecast (37 probes)
- v0.5.0: Semantic Memory Search + Live Telemetry/Anomaly Detection (110 probes)
- v0.1.0: Initial public scaffold, evaluation harness, demo, whitepaper

### Probe summary

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
| **Total** | **174** |

### Non-claims

This framework does not claim machine consciousness, sentience, or subjective
experience. It implements and measures persistent state, distributed cognition,
recursive self-modeling, and emergent module coordination.
