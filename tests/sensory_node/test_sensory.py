from __future__ import annotations

import time
from pathlib import Path

from core.memory.store import Event
from nodes.sensory_node import (
    CodeEncoder,
    LatentProjector,
    PerceivedText,
    SensoryEncoder,
    SensoryPipeline,
    TelemetryEncoder,
)


def _write_sample_module(path: Path) -> None:
    path.write_text(
        '"""Module docstring."""\n\n'
        "class SampleClass:\n"
        '    """Class docstring."""\n'
        "    pass\n\n"
        "def sample_function(value: int) -> int:\n"
        '    """Function docstring."""\n'
        "    return value\n",
        encoding="utf-8",
    )


def test_code_encoder_extracts_signatures(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    _write_sample_module(target)

    perceived = CodeEncoder().encode_file(target)

    assert perceived is not None
    assert "class SampleClass:" in perceived.content
    assert "def sample_function(value: int) -> int:" in perceived.content


def test_code_encoder_extracts_docstrings(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    _write_sample_module(target)

    perceived = CodeEncoder().encode_file(target)

    assert perceived is not None
    assert "module:Module docstring." in perceived.content
    assert "sample_function:Function docstring." in perceived.content


def test_code_encoder_missing_file(tmp_path: Path) -> None:
    assert CodeEncoder().encode_file(tmp_path / "missing.py") is None


def test_code_encoder_skips_non_python(tmp_path: Path) -> None:
    target = tmp_path / "notes.txt"
    target.write_text("hello", encoding="utf-8")

    assert CodeEncoder().encode_file(target) is None


def test_code_encoder_directory_walk(tmp_path: Path) -> None:
    root = tmp_path / "src"
    root.mkdir()
    _write_sample_module(root / "alpha.py")
    (root / "tests").mkdir()
    _write_sample_module(root / "tests" / "ignored.py")

    perceived = CodeEncoder().encode_directory(root)

    assert perceived
    assert all(isinstance(item, PerceivedText) for item in perceived)
    assert perceived[0].source_id == "alpha.py"


def test_telemetry_encoder_high_low_labels() -> None:
    perceived = TelemetryEncoder().encode(
        "memory",
        {"high_metric": 0.9, "low_metric": 0.1, "mid_metric": 0.5},
    )

    assert "high_metric=0.900 (high)" in perceived.content
    assert "low_metric=0.100 (low)" in perceived.content
    assert "mid_metric=0.500" in perceived.content
    assert "mid_metric=0.500 (" not in perceived.content


def test_telemetry_encoder_snapshot() -> None:
    snapshot = {
        "node_health": {"memory": 0.9, "router": 0.1},
        "node_trends": {"memory": 0.05, "router": -0.05},
    }

    perceived = TelemetryEncoder().encode_snapshot(snapshot)

    assert len(perceived) == 2
    assert {item.source_id for item in perceived} == {"memory", "router"}
    assert all(item.source_kind == "telemetry" for item in perceived)


def test_sensory_encoder_flat() -> None:
    perceived = SensoryEncoder().encode({"alpha": 1, "beta": True}, source_id="flat")

    assert "alpha=1" in perceived.content
    assert "beta=True" in perceived.content


def test_sensory_encoder_nested() -> None:
    perceived = SensoryEncoder().encode({"a": {"b": 1}}, source_id="nested")

    assert "a.b=1" in perceived.content


def test_sensory_encoder_truncation() -> None:
    perceived = SensoryEncoder().encode({"text": "x" * 600}, source_id="truncated")

    assert perceived.content.endswith("...[truncated]")
    assert len(perceived.content) == 512


def test_latent_projector_similarity_self() -> None:
    projector = LatentProjector()
    perceived = PerceivedText("code", "shared signal", "module.py", time.time())
    projector.add(perceived)

    assert projector.similarity(perceived, perceived) == 1.0


def test_latent_projector_cross_modal() -> None:
    projector = LatentProjector()
    code = PerceivedText("code", "cache latency shared token", "code.py", time.time())
    telemetry = PerceivedText("telemetry", "cache latency alert", "telemetry", time.time())
    projector.add(code)
    projector.add(telemetry)

    score = projector.similarity(code, telemetry)

    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_latent_projector_search_returns_sorted() -> None:
    projector = LatentProjector()
    projector.add(PerceivedText("code", "cache cache latency", "a", time.time()))
    projector.add(PerceivedText("telemetry", "cache latency", "b", time.time()))
    projector.add(PerceivedText("sensory", "latency", "c", time.time()))

    results = projector.search("cache latency", top_k=3)

    assert [score for _, score in results] == sorted(
        [score for _, score in results], reverse=True
    )


def test_sensory_pipeline_startup_scan(tmp_path: Path) -> None:
    core_root = tmp_path / "core"
    core_root.mkdir()
    _write_sample_module(core_root / "module.py")

    results = SensoryPipeline(core_root=core_root).run_startup_scan()

    assert isinstance(results, list)
    assert len(results) == 1


class _RecordingMemoryStore:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def append(self, event: Event) -> None:
        self.events.append(event)


def test_sensory_pipeline_memory_append(tmp_path: Path) -> None:
    core_root = tmp_path / "core"
    core_root.mkdir()
    _write_sample_module(core_root / "module.py")
    memory_store = _RecordingMemoryStore()

    SensoryPipeline(core_root=core_root, memory_store=memory_store).run_startup_scan()

    assert memory_store.events
    assert memory_store.events[0].event_type == "sensory_perception"
