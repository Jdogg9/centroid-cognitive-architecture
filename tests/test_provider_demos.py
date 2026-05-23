from __future__ import annotations

from examples.run_provider_comparison import comparison_lines
from examples.run_provider_demo import main as provider_demo_main


def test_provider_comparison_demo_is_deterministic() -> None:
    output = "\n".join(comparison_lines())
    assert "Provider comparison" in output
    assert "mock: responses=False" in output
    assert "ollama: responses=True" in output
    assert "vllm: responses=False" in output
    assert "centroid_owns_safety=true" in output


def test_provider_demo_runs_with_mock(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_provider_demo.py",
            "--config",
            "templates/minimal_agent.json",
            "--scenario",
            "operations-observer",
            "--state-dir",
            str(tmp_path),
        ],
    )
    assert provider_demo_main() == 0
