# Limitations

Centroid is an early public reference framework. It is designed to make
persistent cognitive-architecture claims measurable and reproducible, but it is
not a full production runtime or live multi-node deployment.

## Current Constraints

- The default demos are local and deterministic, not a live multi-machine mesh.
- Benchmarks are deterministic reference benchmarks, not hardware-normalized
  deployment benchmarks.
- The 29 baseline probes are deterministic contract checks over fixtures,
  synthetic Holly scenarios, config-driven runtime scenarios, and mock-provider
  boundary paths. They are not live distributed execution evidence.
- Config-driven behavior is implemented for deterministic scenarios: routing,
  safety outcomes, memory retention, and audit provenance can vary by agent
  configuration without core runtime code edits.
- Provider adapter boundaries are implemented for deterministic mock mode and
  opt-in provider paths. Mock mode is what CI verifies.
- Optional live providers are not quality, latency, reliability, or safety
  claims. No live model backend is required or evaluated by default.
- Provider output remains untrusted. Provider tool proposals are normalized,
  safety-evaluated, and audited, but not executed.
- Holly is a deterministic reference agent configuration, not a production
  assistant or non-public persona.
- Longitudinal identity drift is represented by small fixtures, not extended
  multi-week traces.
- Distributed coordination is simulated through deterministic event shape and
  probe checks.
- Shutdown compliance is documented and policy-fixtured, but not yet exercised
  against a live long-running process.

## Known Future Validation Areas

- live provider quality, latency, reliability, and provider-failure behavior
- adversarial robustness and prompt/tool-proposal abuse fixtures
- live tool execution with approval-gated mutating boundaries
- live distributed mesh execution and failure injection
- long-horizon identity stability and memory compaction loss
- live shutdown validation and rollback verification
- hardware-normalized latency benchmarks
- schema drift across independent implementations

## Non-Claims Boundary

These limitations do not weaken the non-claims boundary. Centroid does not
claim consciousness, sentience, subjective phenomenology, autonomous personhood,
subjective experience, autonomous moral agency, self-preservation rights, or
validated scientific proof of subjective experience.
