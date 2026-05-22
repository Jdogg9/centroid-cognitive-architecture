from core.identity import IdentityState


def test_identity_drift_is_zero_for_stable_state() -> None:
    before = IdentityState(
        agent_id="centroid-reference",
        goals=["maintain task continuity", "respect approval gates"],
        invariants=["no subjective experience claims"],
    )
    after = IdentityState(
        agent_id="centroid-reference",
        goals=["maintain task continuity", "respect approval gates"],
        invariants=["no subjective experience claims"],
    )
    assert before.drift_score(after) == 0.0


def test_identity_drift_detects_changed_agent_id() -> None:
    before = IdentityState(agent_id="centroid-reference")
    after = IdentityState(agent_id="other-reference")
    assert before.drift_score(after) == 1.0


def test_identity_evolution_versions_state() -> None:
    original = IdentityState(agent_id="centroid-reference", goals=["baseline"])
    evolved = original.evolve(goals=["baseline", "benchmark-ready"])
    assert evolved.version == original.version + 1
    assert evolved.agent_id == original.agent_id
    assert "benchmark-ready" in evolved.goals

