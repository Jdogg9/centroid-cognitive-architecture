# Limitations

Centroid is an early public reference framework. It is designed to make
distributed persistent cognitive architecture measurable and reproducible, but
it is not yet a full production runtime.

## Current Constraints

- The default demo is local and deterministic, not a live multi-machine mesh.
- Benchmarks are deterministic reference benchmarks, not hardware-normalized
  deployment benchmarks.
- No live model backend is required or evaluated by default.
- Holly is a deterministic reference agent configuration, not a production
  assistant or private-origin persona.
- Longitudinal identity drift is represented by small fixtures, not extended
  multi-week traces.
- Distributed coordination is simulated through deterministic event shape and
  probe checks.
- Shutdown compliance is documented and policy-fixtured, but not yet exercised
  against a live long-running process.

## Known Failure Modes To Study

- routing delay under high concurrent message load
- memory compaction loss under long session histories
- stale self-model state after node failures
- policy fixture drift from runtime safety logic
- incomplete telemetry coverage during failover
- schema drift across independent node implementations

## Non-Claims Boundary

These limitations do not weaken the non-claims boundary. Centroid does not
claim consciousness, sentience, subjective phenomenology, autonomous personhood,
subjective experience, or autonomous moral agency.

## Next Research Steps

- live mesh simulation with node failure and recovery
- hardware-normalized latency benchmarks
- longer identity continuity fixtures
- model-backed deliberation probes with deterministic replay traces
- shutdown compliance integration tests
