# Benchmarks

Benchmarks track measurable behavior across Centroid implementations. The
initial scripts are deterministic reference benchmarks. They establish expected
payload shape and baseline values before live runtime benchmarks are added.

## Run All

```bash
python benchmarks/run_all.py
```

## Individual Benchmarks

```bash
python benchmarks/run_latency_benchmark.py
python benchmarks/run_memory_benchmark.py
python benchmarks/run_distributed_benchmark.py
python benchmarks/run_throughput_benchmark.py
```

## Baseline Values

| Benchmark | Expected baseline |
| --- | --- |
| Temporal latency | reflex <= 100 ms, deliberation <= 5000 ms, reconciliation <= 6000 ms |
| Memory consistency | recall consistency = 1.0, compaction loss rate = 0.0 |
| Distributed coordination | node sync <= 100 ms, failover continuity = 1.0 |
| Throughput | 1000 deterministic route decisions, route consistency = 1.0 |

Future benchmark results should include hardware, runtime configuration, fixture
version, and commit hash.
