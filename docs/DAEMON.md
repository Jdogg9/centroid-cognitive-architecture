# Live Daemon Loop

## Overview

The Centroid daemon is a synchronous, auditable runtime loop for sequencing the architecture's live modules. It does not make autonomous decisions, spawn threads, or use asyncio. Each cycle calls the configured modules in order, records a cycle result, and appends one `cycle_complete` event to memory when a `MemoryStore` is configured.

All modules are optional. Missing or disabled modules are skipped silently so the daemon can run against partial local setups, test doubles, or progressively wired deployments.

## Quick start

```bash
python3 examples/run_daemon.py --dry-run
```

`--dry-run` loads `config/daemon.yaml` or creates defaults when missing, runs exactly three cycles, prints readable `CycleResult` summaries, and exits non-zero if any cycle reports errors.

## Configuration

| Field | Default | Description |
|---|---:|---|
| `tick_interval_s` | `5.0` | Seconds between cycle starts. |
| `max_cycles` | `null` | Stop after this many cycles; `null` runs until signaled. |
| `startup_delay_s` | `0.0` | Optional delay before the first cycle. |
| `state_dir` | `state/` | Directory for world snapshots, calibration, and plan state. |
| `coherence_graph_path` | `config/coherence_graph.yaml` | Module coherence graph config path. |
| `memory_store_path` | `state/memory.jsonl` | Append-only JSONL memory event path. |
| `enable_sensory` | `true` | Run the startup sensory scan on cycle 0. |
| `enable_coherence` | `true` | Run coherence graph propagation. |
| `enable_forecast` | `true` | Generate calibrated forecasts. |
| `enable_feedback` | `true` | Resolve mature forecasts against actual values. |

## Cycle sequence

1. Sensory: `SensoryPipeline.run_startup_scan()` on cycle 0 only.
2. Self-model: `SelfModel.tick()` writes and returns a `WorldSnapshot`.
3. Coherence: `CoherenceGraph.tick()` reads latest health scores and returns a `CoherenceReport`.
4. Forecast: `ForecastGenerator.generate(current_values, calibration_store)` returns forecasts and registers them with feedback when available.
5. Feedback: `ForecastFeedbackLoop.resolve(actual_values)` returns matured `FeedbackResult` entries.
6. Memory append: one `cycle_complete` event records cycle number, duration, coherence index, anomaly count, and timestamp.

## Graceful shutdown

`SIGINT` and `SIGTERM` set a stop flag. The scheduler never interrupts a cycle in progress; it exits only after the current cycle returns and logs `daemon stopped after N cycles`.

## Error handling

Each step is wrapped in `try/except Exception`. A module failure is recorded in `CycleResult.errors` with the step name, and the remaining steps continue. This fault isolation makes daemon runs useful for diagnostics without masking which module failed.

## Integration with evaluation

After a live daemon session, run the full evaluation harness to verify state file integrity and behavioral contracts:

```bash
python3 examples/run_evaluation.py --mode full --suite all
```

The daemon's default writes stay within the existing state files used by the self-model, coherence, planner calibration, plan tree, and memory store.
