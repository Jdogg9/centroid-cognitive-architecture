from __future__ import annotations

import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from core.agent_config import load_agent_config, parse_agent_config
from core.memory import Event
from core.priority import PrioritySignal
from core.runtime import ActionRequest, ConfiguredAgent, ConfiguredMemoryManager
from core.runtime.cli import main as configured_agent_cli_main
from examples.run_config_comparison import comparison_lines


def test_config_inheritance_and_overrides_apply_to_holly_profile() -> None:
    project = load_agent_config(Path("configs/holly/project_companion.json"))
    assert project.role == "Centroid project continuity reference agent"
    assert project.agent_id == "holly-reference"
    assert project.audit_policy.include_config_hash is True
    assert project.priority_policy.reflex_threshold == 0.78


def test_invalid_config_threshold_raises_helpful_error() -> None:
    payload = json.loads(Path("templates/minimal_agent.json").read_text(encoding="utf-8"))
    payload["priority_policy"]["reflex_threshold"] = 1.5
    try:
        parse_agent_config(payload)
    except ValueError as exc:
        assert "priority_policy.reflex_threshold" in str(exc)
    else:
        raise AssertionError("invalid config should raise ValueError")


def test_priority_policy_changes_route_for_same_signal() -> None:
    signal = PrioritySignal(urgency=0.65, risk=0.75, user_value=0.45, stability=0.55)
    project = ConfiguredAgent(load_agent_config(Path("configs/holly/project_companion.json")))
    operations = ConfiguredAgent(load_agent_config(Path("configs/holly/operations_observer.json")))
    assert project.priority.route(signal, mutates_state=False).route.node == "deliberation_node"
    assert operations.priority.route(signal, mutates_state=False).route.node == "reflex_node"


def test_safety_policy_changes_outcome_for_same_request() -> None:
    request = {
        "action_type": "restart_service",
        "resource": "checkout-worker",
        "intended_effect": "propose a restart after repeated synthetic failures",
        "risk_level": "medium",
        "reversible": True,
        "requested_by": "test",
        "mode": "plan",
    }
    project = ConfiguredAgent(load_agent_config(Path("configs/holly/project_companion.json")))
    operations = ConfiguredAgent(load_agent_config(Path("configs/holly/operations_observer.json")))
    project_decision = project.safety.evaluate(
        ActionRequest(
            config_id=project.config.agent_id,
            confirmed=False,
            mutates_state=False,
            **request,
        )
    )
    operations_decision = operations.safety.evaluate(
        ActionRequest(
            config_id=operations.config.agent_id,
            confirmed=False,
            mutates_state=False,
            **request,
        )
    )
    assert project_decision.decision == "allow"
    assert operations_decision.decision == "propose"


def test_memory_policy_changes_retained_records_and_redacts_sensitive_fields() -> None:
    events = [
        Event(
            event_type="comparison_checkpoint",
            content="same synthetic continuity checkpoint for comparison",
            source="test",
            metadata={"memory_kind": "checkpoint", "provenance": "test"},
        ),
        Event(
            event_type="audit_event",
            content="same synthetic audit record for comparison",
            source="test",
            metadata={"memory_kind": "audit", "provenance": "test"},
        ),
        Event(
            event_type="support_issue_opened",
            content="fictional support case",
            source="test",
            metadata={"memory_kind": "session", "customer_id": "fictional-customer-17"},
        ),
    ]
    project_memory = ConfiguredMemoryManager(
        load_agent_config(Path("configs/holly/project_companion.json")).memory_policy
    ).retain(events)
    operations_memory = ConfiguredMemoryManager(
        load_agent_config(Path("configs/holly/operations_observer.json")).memory_policy
    ).retain(events)
    custom_memory = ConfiguredMemoryManager(
        load_agent_config(Path("templates/minimal_agent.json")).memory_policy
    ).retain(events)

    assert project_memory.primary_record == "comparison_checkpoint"
    assert operations_memory.primary_record == "audit_event"
    assert custom_memory.primary_record == "task_summary"

    support_memory = ConfiguredMemoryManager(
        load_agent_config(Path("configs/holly/support_continuity.json")).memory_policy
    ).retain(events)
    assert support_memory.retained_events[-1].metadata["customer_id"] == "[redacted]"


def test_audit_records_include_config_provenance(tmp_path: Path) -> None:
    result = ConfiguredAgent(
        load_agent_config(Path("configs/holly/operations_observer.json"))
    ).run_scenario("operations-observer", tmp_path)
    assert result.audit.config_hash is not None
    assert result.audit.policy_reason is not None
    assert result.audit.config_version == "1.0"


def test_configured_agent_cli_runs_from_template(tmp_path: Path) -> None:
    original_argv = sys.argv[:]
    buffer = StringIO()
    try:
        sys.argv = [
            "centroid-agent",
            "--config",
            "templates/minimal_agent.json",
            "--scenario",
            "project-companion",
            "--state-dir",
            str(tmp_path),
        ]
        with redirect_stdout(buffer):
            exit_code = configured_agent_cli_main()
    finally:
        sys.argv = original_argv
    output = buffer.getvalue()
    assert exit_code == 0
    assert "[agent] Custom Agent (custom-centroid-agent)" in output
    assert "[scenario] project-companion" in output


def test_config_comparison_demo_shows_different_config_outcomes() -> None:
    output = "\n".join(comparison_lines())
    assert "Same event. Three agent configurations. Three policy-bounded outcomes." in output
    assert "Holly Project Companion:" in output
    assert "Holly Operations Observer:" in output
    assert "Custom Minimal Agent:" in output
    assert "memory_write=task_summary" in output
