# Changelog

## v0.4.1 - 2026-05-23

- Repair release CI checks after the pushed `v0.4.0` tag failed on CI-only workflow issues: a stale provider-schema pytest node id and an overbroad credential/private-endpoint grep that matched safe source-code symbols and a numbered documentation heading.
- Keep the provider-adapter implementation unchanged: deterministic mock-provider verification, 29 baseline probes at score 1.0000, no provider tool execution, and MCP deferred to v0.5.0.
- Intended publishable provider-adapter release after the `v0.4.0` tagged build failed CI; the existing public `v0.4.0` tag is not moved.

## v0.4.0 - 2026-05-23

- Add a provider-neutral model adapter layer with deterministic mock, optional OpenAI, optional Anthropic, and OpenAI-compatible Ollama/vLLM profiles.
- Route provider text and tool proposals through the configured Centroid runtime while preserving Centroid authority over continuity, memory policy, routing, safety, audit provenance, and action gating.
- Add provider schemas, public-safe provider config examples, placeholder `.env.example`, provider demos, and provider CLI selection for `centroid-agent` and Holly.
- Expand deterministic evaluation coverage from 23 to 29 probes for provider contracts, declared capabilities, tool-proposal safety gating, audit redaction, mock runtime execution, and source-environment provider CLI execution.
- Document that live providers are opt-in only, CI verifies mock behavior only, provider tool proposals do not execute, and MCP remains future v0.5.0 work.

## v0.3.0 - 2026-05-22

- Add a config-driven runtime layer under `core/runtime/` for routing, safety,
  memory retention, and audit provenance.
- Extend the agent configuration schema with config versioning, structured
  priority policy, structured safety policy, configurable memory retention, and
  audit policy fields.
- Add inheritance-aware config loading so Holly scenario profiles can extend the
  shared base config without duplicating all policy data.
- Add a neutral `centroid-agent` CLI for running any packaged or local agent
  config against the deterministic public scenarios.
- Add a deterministic config-comparison demo showing the same synthetic input
  producing different routes, memory writes, and safety outcomes under
  different configs.
- Expand baseline evaluation coverage from 17 to 23 deterministic probes,
  including config-driven routing, safety, memory, CLI, audit, and Holly
  backward-compatibility checks.
- Extend wheel smoke coverage and CI to exercise `centroid-agent` and the
  config-comparison demo alongside the existing Holly and evaluation paths.

## v0.2.0 - Holly Reference Agent

- Introduced Holly as Centroid's configurable public reference agent.
- Added six deterministic Holly scenarios: project companion, support
  continuity, operations observer, temporal layering, persistent identity, and
  safety gate.
- Added schema-backed Holly configs and minimal custom-agent templates.
- Expanded deterministic evaluation coverage from 11 to 17 probes.
- Preserved explicit safety and non-claims boundaries.

## v0.1.0 - Initial Public Release

- Published the initial Centroid Cognitive Architecture scaffold.
- Added core identity, memory, routing, safety, temporal, self-model, and
  evaluation modules.
- Added public documentation, diagrams, schemas, deterministic demos, and
  baseline evaluation fixtures.
