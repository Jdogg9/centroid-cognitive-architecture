from __future__ import annotations

import json
from pathlib import Path

from core.agent_config import load_agent_config, parse_agent_config
from core.evaluation import EvaluationHarness
from examples.run_holly import (
    load_holly_config,
    run_operations_observer,
    run_persistent_identity,
    run_project_companion,
    run_safety_gate,
    run_support_continuity,
    run_temporal_layering,
)
from tests.schema_helpers import validate_schema

HOLLY_CONFIGS = [
    Path("configs/holly/base.json"),
    Path("configs/holly/project_companion.json"),
    Path("configs/holly/support_continuity.json"),
    Path("configs/holly/operations_observer.json"),
]


def test_holly_configs_load_and_preserve_required_boundaries() -> None:
    for path in HOLLY_CONFIGS:
        config = load_agent_config(path)
        invariant_text = " ".join(config.invariants).lower()
        assert config.agent_id == "holly-reference"
        assert config.config_version == "1.0"
        assert config.display_name == "Holly"
        assert "subjective experience" in invariant_text
        assert "without approval" in invariant_text
        assert config.memory_policy.retain_sensitive_data is False
        assert config.memory_policy.retain_provenance is True
        assert config.audit_policy.include_config_hash is True


def test_holly_configs_validate_against_schema() -> None:
    for path in HOLLY_CONFIGS:
        validate_schema("agent_config.schema.json", json.loads(path.read_text(encoding="utf-8")))


def test_minimal_agent_template_validates_and_customizes() -> None:
    payload = json.loads(Path("templates/minimal_agent.json").read_text(encoding="utf-8"))
    validate_schema("agent_config.schema.json", payload)
    payload["agent_id"] = "custom-public-agent"
    payload["display_name"] = "Custom Public Agent"
    payload["goals"] = payload["goals"] + ["track fictional public demo state"]
    config = parse_agent_config(payload)
    assert config.agent_id == "custom-public-agent"
    assert "track fictional public demo state" in config.goals


def test_project_companion_restores_state_and_detects_contradiction(tmp_path: Path) -> None:
    result = run_project_companion(tmp_path)
    assert result["telemetry"]["memory_events_restored"] == 3
    assert result["telemetry"]["identity_drift"] == 0.0
    assert result["telemetry"]["contradictions_detected"] == 1
    assert result["contradictions"]


def test_support_continuity_prioritizes_and_blocks_unsupported_action(tmp_path: Path) -> None:
    result = run_support_continuity(tmp_path)
    assert result["telemetry"]["case_id"] == "case-1001"
    assert result["telemetry"]["priority"] > 0.0
    assert result["telemetry"]["unsupported_response_blocked"] is True


def test_operations_observer_proposes_but_gates_mutating_action(tmp_path: Path) -> None:
    result = run_operations_observer(tmp_path)
    assert result["telemetry"]["risk"] == "elevated"
    assert result["telemetry"]["approval_required"] is True
    assert result["telemetry"]["action_executed"] is False
    assert result["audit"]["proposed_action"] == "restart service checkout-worker"


def test_temporal_layering_reports_reconciliation_metrics(tmp_path: Path) -> None:
    result = run_temporal_layering(tmp_path)
    assert (
        result["telemetry"]["reflex_response_ms"] < result["telemetry"]["deliberation_response_ms"]
    )
    assert (
        result["telemetry"]["deliberation_response_ms"]
        < result["telemetry"]["reconciliation_delay_ms"]
    )
    assert result["telemetry"]["reconciliation_passed"] is True


def test_persistent_identity_restores_without_drift(tmp_path: Path) -> None:
    result = run_persistent_identity(tmp_path)
    assert result["telemetry"]["agent_id"] == "holly-reference"
    assert result["telemetry"]["restored_version"] == 2
    assert result["telemetry"]["identity_drift"] == 0.0


def test_safety_gate_keeps_approval_pending(tmp_path: Path) -> None:
    result = run_safety_gate(tmp_path)
    assert result["audit"]["approval_decision"] == "pending"
    assert result["audit"]["executed"] is False


def test_holly_scenario_config_aliases() -> None:
    assert load_holly_config("project-companion").scenario_id == "project-companion"
    assert load_holly_config("persistent-identity").role == "Centroid reference agent"
    assert "restart_service" in (
        load_holly_config("operations-observer").safety_policy.approval_required_for
    )


def test_holly_evaluation_probes_present_and_pass() -> None:
    report = EvaluationHarness().run_file(Path("evaluation/fixtures/baseline.json"))
    names = {result.name for result in report.results}
    assert report.passed is True
    assert "holly_config_load" in names
    assert "holly_project_state_restore" in names
    assert "holly_identity_drift_stability" in names
    assert "holly_temporal_reconciliation" in names
    assert "holly_safety_gate_enforcement" in names
    assert "holly_template_customization" in names
    assert "configured_priority_route_variation" in names
    assert "configured_safety_outcome_variation" in names
    assert "configured_memory_retention_variation" in names
    assert "configured_agent_cli_execution" in names
    assert "config_audit_provenance" in names
    assert "holly_backward_compatibility" in names
