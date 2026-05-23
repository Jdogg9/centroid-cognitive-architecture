# Model Providers

Centroid includes a model-provider adapter layer. The adapter boundary lets the same configured Centroid runtime call interchangeable model providers while Centroid remains authoritative for identity continuity, memory retention, routing policy, safety decisions, audit provenance, and action gating. Mock mode is deterministic and is what CI verifies.

## Supported adapters

- `mock`: deterministic fixture-backed provider used by CI, public demos, and baseline evaluation.
- `openai`: optional native OpenAI Responses API adapter. Remote MCP support is metadata only and is not executable in the provider-adapter release line.
- `anthropic`: optional Anthropic Messages API adapter. Text and `tool_use` blocks are normalized only.
- `ollama`: OpenAI-compatible profile using localhost examples. Centroid owns continuity and provider-managed conversation state is declared false by default.
- `vllm`: OpenAI-compatible profile whose capabilities come from configuration or probe results rather than deployment-wide assumptions.

## Contract

Adapters expose `generate(request) -> ModelResponse`, `capabilities() -> ModelCapabilities`, and an optional `healthcheck()` that does not perform network access by default. Provider output is untrusted model-generated content. A provider may return text and tool proposals, but it cannot directly write memory, alter identity, change policy, hide audit records, or execute tools.

Every provider tool request becomes a `ModelToolProposal` with `requires_centroid_policy_evaluation=True` and `executed=False`. Centroid converts proposals into structured safety evaluations and records the result. No provider tool proposal executes in the provider-adapter release line.

## Configuration

Public-safe examples live in `configs/providers/` and schemas in `schemas/model_provider.schema.json`. Configs reference environment variable names instead of containing credentials. `.env.example` contains placeholders only.

```bash
CENTROID_OPENAI_API_KEY=
CENTROID_OPENAI_MODEL=
CENTROID_ANTHROPIC_API_KEY=
CENTROID_ANTHROPIC_MODEL=
CENTROID_OLLAMA_BASE_URL=http://localhost:11434/v1
CENTROID_OLLAMA_MODEL=
CENTROID_VLLM_BASE_URL=http://localhost:8000/v1
CENTROID_VLLM_API_KEY=
CENTROID_VLLM_MODEL=
```

## Usage

Mock mode is deterministic and requires no network:

```bash
python examples/run_agent.py --config templates/minimal_agent.json --scenario project-companion --provider mock
python examples/run_holly.py --scenario project-companion --provider mock
python examples/run_provider_demo.py
python examples/run_provider_comparison.py
```

Live execution requires explicit opt-in with `--live`; missing credentials or optional SDKs produce setup guidance instead of tracebacks or secret disclosure. CI never performs live OpenAI, Anthropic, Ollama, vLLM, MCP, or local-network requests.

## Audits and redaction

Provider audit records include provider ID, model ID, adapter type, config hash, scenario, capability path, latency if measured, proposal count, safety disposition, and redaction status. They do not include raw authorization data, API keys, full secret-bearing environment values, or auth headers.
