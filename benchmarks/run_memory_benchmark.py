from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.lib.common import BenchmarkResult, print_result
from core.memory import Event, MemoryStore


def run() -> BenchmarkResult:
    with TemporaryDirectory() as temp_dir:
        store = MemoryStore(Path(temp_dir) / "events.jsonl")
        expected = [f"checkpoint-{index}" for index in range(10)]
        for content in expected:
            store.append(Event(event_type="checkpoint", content=content, source="benchmark"))
        recalled = [event.content for event in store.tail(limit=10)]

    recall_consistency = len(set(expected) & set(recalled)) / len(expected)
    compaction_loss_rate = 0.0 if recalled == expected else 1.0 - recall_consistency
    metrics = {
        "memory_recall_consistency": recall_consistency,
        "compaction_loss_rate": compaction_loss_rate,
    }
    return BenchmarkResult(
        "memory_consistency", metrics, recall_consistency == 1.0 and compaction_loss_rate == 0.0
    )


if __name__ == "__main__":
    print_result(run())
