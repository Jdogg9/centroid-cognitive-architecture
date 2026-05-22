from pathlib import Path

from examples.run_demo import (
    initialize_agent,
    memory_interaction,
    route_demo_inputs,
    run_baseline_evaluation,
    run_demo,
    safety_gate_check,
    update_self_model,
)


def test_demo_components(tmp_path: Path) -> None:
    identity, self_model = initialize_agent(tmp_path)
    assert identity.agent_id == "centroid-demo"
    assert self_model.status == "healthy"

    routed = route_demo_inputs()
    assert routed[0]["node"] == "reflex_node"
    assert routed[1]["node"] == "deliberation_node"

    memory = memory_interaction(tmp_path)
    assert memory["classification"] == "privileged"

    updated = update_self_model(tmp_path, self_model)
    assert "baseline evaluation ready" in updated.active_goals

    gate = safety_gate_check()
    assert gate["result"] == "hold"
    assert gate["requires_approval"] is True


def test_full_demo_passes(tmp_path: Path) -> None:
    assert run_demo("full", tmp_path) == 0


def test_minimal_demo_passes(tmp_path: Path) -> None:
    assert run_demo("minimal", tmp_path) == 0


def test_demo_evaluation_passes() -> None:
    report = run_baseline_evaluation()
    assert report["passed"] is True
    assert report["probe_count"] == 11
