from benchmarks.run_all import main as run_all_main
from benchmarks.run_distributed_benchmark import run as run_distributed
from benchmarks.run_latency_benchmark import run as run_latency
from benchmarks.run_memory_benchmark import run as run_memory
from benchmarks.run_throughput_benchmark import run as run_throughput


def test_benchmarks_pass() -> None:
    for benchmark in (run_latency(), run_memory(), run_distributed(), run_throughput()):
        assert benchmark.passed is True


def test_run_all_benchmarks() -> None:
    assert run_all_main() == 0
