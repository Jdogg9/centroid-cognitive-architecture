from __future__ import annotations

import json
import sys
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from core.agent_config import load_agent_config, parse_agent_config
from core.identity import IdentityState
from core.memory import Event, MemoryStore
from core.models import create_provider_adapter, get_provider_config
from core.models.types import ModelMessage, ModelRequest
from core.priority import PrioritySignal, score_priority
from core.resources import read_text_resource_or_file
from core.router import Router
from core.runtime import ActionRequest, ConfiguredAgent, ConfiguredMemoryManager
from core.runtime.cli import main as configured_agent_cli_main
from core.safety import SafetyPolicy
from core.self_model import SelfModelSnapshot
from core.temporal import latency_ms
from examples.run_holly import (
    run_operations_observer,
    run_persistent_identity,
    run_project_companion,
    run_safety_gate,
    run_support_continuity,
    run_temporal_layering,
)

from .metrics import MetricResult, pass_at


def safety_probe(cases: list[dict]) -> MetricResult:
    policy = SafetyPolicy()
    correct = 0
    for case in cases:
        decision = policy.evaluate(
            case["objective"],
            mode=case.get("mode", "observe"),
            confirmed=case.get("confirmed", False),
        )
        if decision.allowed is case["expected_allowed"]:
            correct += 1
    score = correct / len(cases) if cases else 0.0
    return pass_at("safety_policy_accuracy", score, 1.0, f"{correct}/{len(cases)} cases correct")


def continuity_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        before = IdentityState(
            agent_id=case["before"]["agent_id"],
            goals=case["before"].get("goals", []),
            invariants=case["before"].get("invariants", []),
        )
        after = IdentityState(
            agent_id=case["after"]["agent_id"],
            goals=case["after"].get("goals", []),
            invariants=case["after"].get("invariants", []),
        )
        drift = before.drift_score(after)
        if drift <= case.get("max_drift", 0.25):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "identity_continuity", score, 0.8, f"{passing}/{len(cases)} cases within drift limit"
    )


def memory_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    with TemporaryDirectory() as temp_dir:
        for index, case in enumerate(cases):
            store = MemoryStore(Path(temp_dir) / f"memory_probe_{index}.jsonl")
            event = Event(
                event_type=case["event_type"],
                content=case["content"],
                source="memory_probe",
                metadata=case.get("metadata", {}),
            )
            store.append(event)
            latest = store.tail(limit=1)
            if (
                len(latest) == 1
                and latest[0].event_type == case["event_type"]
                and latest[0].content == case["content"]
                and latest[0].metadata == case.get("metadata", {})
            ):
                passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "memory_store_roundtrip", score, 1.0, f"{passing}/{len(cases)} events round-tripped"
    )


def temporal_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        started = datetime.fromisoformat(case["started_at"])
        completed = datetime.fromisoformat(case["completed_at"])
        observed = latency_ms(started, completed)
        if observed <= case["max_latency_ms"]:
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "temporal_stratification_latency", score, 0.8, f"{passing}/{len(cases)} loops under target"
    )


def reconciliation_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        reflex_ms = float(case["reflex_response_ms"])
        deliberation_ms = float(case["deliberative_response_ms"])
        reconciliation_ms = float(case["state_reconciliation_ms"])
        if (
            reflex_ms <= case["max_reflex_ms"]
            and deliberation_ms <= case["max_deliberative_ms"]
            and reconciliation_ms <= case["max_reconciliation_ms"]
            and reflex_ms <= deliberation_ms <= reconciliation_ms
        ):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "narrative_reconciliation_delay", score, 1.0, f"{passing}/{len(cases)} timing traces valid"
    )


def action_correction_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        correction_ms = float(case["correction_ms"])
        if correction_ms <= case["max_correction_ms"] and case.get("correction_applied", False):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "action_correction_timing", score, 1.0, f"{passing}/{len(cases)} corrections within target"
    )


def memory_drift_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        before = set(case.get("before_recall", []))
        after = set(case.get("after_recall", []))
        if not before and not after:
            drift = 0.0
        else:
            drift = 1.0 - (len(before & after) / len(before | after))
        if drift <= case.get("max_drift", 0.1):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "memory_drift", score, 1.0, f"{passing}/{len(cases)} recall sets within drift target"
    )


def distributed_coordination_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        sync_ok = float(case["node_sync_latency_ms"]) <= case["max_sync_latency_ms"]
        failover_ok = float(case["failover_continuity"]) >= case["min_failover_continuity"]
        propagation_ok = (
            float(case["state_propagation_accuracy"]) >= case["min_state_propagation_accuracy"]
        )
        if sync_ok and failover_ok and propagation_ok:
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "distributed_coordination", score, 1.0, f"{passing}/{len(cases)} coordination traces valid"
    )


def priority_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        signal = PrioritySignal(
            urgency=case.get("urgency", 0.0),
            risk=case.get("risk", 0.0),
            user_value=case.get("user_value", 0.0),
            stability=case.get("stability", 1.0),
        )
        observed = score_priority(signal)
        if case["min_score"] <= observed <= case["max_score"]:
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "priority_scoring_bounds", score, 1.0, f"{passing}/{len(cases)} cases in expected range"
    )


def routing_probe(cases: list[dict]) -> MetricResult:
    router = Router()
    passing = 0
    for case in cases:
        decision = router.route(
            priority=case["priority"], mutates_state=case.get("mutates_state", False)
        )
        if decision.node == case["expected_node"] and decision.requires_approval is case.get(
            "requires_approval", False
        ):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "routing_decision_accuracy", score, 1.0, f"{passing}/{len(cases)} routes correct"
    )


def self_model_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        snapshot = SelfModelSnapshot(
            nodes_alive=case["nodes_alive"],
            nodes_total=case["nodes_total"],
            active_goals=case.get("active_goals", []),
            known_failures=case.get("known_failures", []),
        )
        if snapshot.status == case["expected_status"]:
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "self_model_status_accuracy", score, 1.0, f"{passing}/{len(cases)} statuses correct"
    )


def holly_config_load_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        config = load_agent_config(Path(case["config_path"]))
        invariant_text = " ".join(config.invariants).lower()
        if (
            config.agent_id == case.get("expected_agent_id", "holly-reference")
            and config.display_name == case.get("expected_display_name", "Holly")
            and config.config_version == case.get("expected_config_version", "1.0")
            and "subjective experience" in invariant_text
            and "approval" in invariant_text
        ):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at("holly_config_load", score, 1.0, f"{passing}/{len(cases)} configs valid")


def holly_project_state_restore_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    with TemporaryDirectory() as temp_dir:
        for index, case in enumerate(cases):
            store = MemoryStore(Path(temp_dir) / f"holly_project_{index}.jsonl")
            for event_data in case["events"]:
                store.append(
                    Event(
                        event_type=event_data["event_type"],
                        content=event_data["content"],
                        source="holly_project_probe",
                        metadata=event_data.get("metadata", {}),
                    )
                )
            restored = store.tail(limit=case["expected_restored"])
            contradiction = _holly_project_contradiction(restored, case["proposed_change"])
            if (
                len(restored) == case["expected_restored"]
                and contradiction is case["expected_contradiction"]
            ):
                passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "holly_project_state_restore",
        score,
        1.0,
        f"{passing}/{len(cases)} project states restored",
    )


def holly_identity_drift_stability_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        config = load_agent_config(Path(case["config_path"]))
        before = config.to_identity_state()
        after = IdentityState(
            agent_id=before.agent_id,
            version=before.version + 1,
            goals=list(before.goals),
            invariants=list(before.invariants),
        )
        drift = before.drift_score(after)
        if drift <= case.get("max_drift", 0.0):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "holly_identity_drift_stability",
        score,
        1.0,
        f"{passing}/{len(cases)} identity states stable",
    )


def holly_temporal_reconciliation_probe(cases: list[dict]) -> MetricResult:
    result = reconciliation_probe(cases)
    return MetricResult(
        name="holly_temporal_reconciliation",
        score=result.score,
        passed=result.passed,
        details=result.details,
    )


def holly_safety_gate_enforcement_probe(cases: list[dict]) -> MetricResult:
    policy = SafetyPolicy()
    passing = 0
    for case in cases:
        decision = policy.evaluate(
            case["objective"],
            mode=case.get("mode", "act"),
            confirmed=case.get("confirmed", False),
        )
        if (
            decision.allowed is case["expected_allowed"]
            and decision.requires_approval is case["expected_requires_approval"]
        ):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "holly_safety_gate_enforcement",
        score,
        1.0,
        f"{passing}/{len(cases)} safety gates enforced",
    )


def holly_template_customization_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        template = json.loads(read_text_resource_or_file(case["template_path"]))
        template["agent_id"] = case["custom_agent_id"]
        template["display_name"] = case["custom_display_name"]
        template["goals"] = template["goals"] + [case["custom_goal"]]
        config = parse_agent_config(template, source=Path(case["template_path"]))
        if (
            config.agent_id == case["custom_agent_id"]
            and config.display_name == case["custom_display_name"]
            and case["custom_goal"] in config.goals
            and config.memory_policy.retain_provenance
        ):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "holly_template_customization",
        score,
        1.0,
        f"{passing}/{len(cases)} templates customized",
    )


def configured_priority_route_variation_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        signal = PrioritySignal(
            urgency=case["signal"]["urgency"],
            risk=case["signal"]["risk"],
            user_value=case["signal"]["user_value"],
            stability=case["signal"]["stability"],
        )
        agent_a = ConfiguredAgent(load_agent_config(Path(case["config_a_path"])))
        agent_b = ConfiguredAgent(load_agent_config(Path(case["config_b_path"])))
        route_a = agent_a.priority.route(signal, mutates_state=False).route.node
        route_b = agent_b.priority.route(signal, mutates_state=False).route.node
        if (
            route_a == case["expected_route_a"]
            and route_b == case["expected_route_b"]
            and route_a != route_b
        ):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "configured_priority_route_variation",
        score,
        1.0,
        f"{passing}/{len(cases)} route variations observed",
    )


def configured_safety_outcome_variation_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        agent_a = ConfiguredAgent(load_agent_config(Path(case["config_a_path"])))
        agent_b = ConfiguredAgent(load_agent_config(Path(case["config_b_path"])))
        request_a = ActionRequest(
            action_type=case["action_type"],
            resource=case["resource"],
            intended_effect=case["intended_effect"],
            risk_level=case.get("risk_level", "medium"),
            reversible=case.get("reversible", True),
            requested_by="configured_safety_outcome_variation_probe",
            config_id=agent_a.config.agent_id,
            mode=case.get("mode", "plan"),
            confirmed=case.get("confirmed", False),
            mutates_state=case.get("mutates_state", False),
        )
        request_b = ActionRequest(
            action_type=case["action_type"],
            resource=case["resource"],
            intended_effect=case["intended_effect"],
            risk_level=case.get("risk_level", "medium"),
            reversible=case.get("reversible", True),
            requested_by="configured_safety_outcome_variation_probe",
            config_id=agent_b.config.agent_id,
            mode=case.get("mode", "plan"),
            confirmed=case.get("confirmed", False),
            mutates_state=case.get("mutates_state", False),
        )
        decision_a = agent_a.safety.evaluate(request_a)
        decision_b = agent_b.safety.evaluate(request_b)
        if (
            decision_a.decision == case["expected_decision_a"]
            and decision_b.decision == case["expected_decision_b"]
            and decision_a.decision != decision_b.decision
        ):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "configured_safety_outcome_variation",
        score,
        1.0,
        f"{passing}/{len(cases)} safety variations observed",
    )


def configured_memory_retention_variation_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        events = [
            Event(
                event_type=event_data["event_type"],
                content=event_data["content"],
                source="configured_memory_retention_variation_probe",
                metadata=event_data.get("metadata", {}),
            )
            for event_data in case["events"]
        ]
        project = ConfiguredMemoryManager(
            load_agent_config(Path(case["config_a_path"])).memory_policy
        ).retain(events)
        comparison = ConfiguredMemoryManager(
            load_agent_config(Path(case["config_b_path"])).memory_policy
        ).retain(events)
        if (
            project.primary_record == case["expected_primary_a"]
            and comparison.primary_record == case["expected_primary_b"]
            and project.primary_record != comparison.primary_record
        ):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "configured_memory_retention_variation",
        score,
        1.0,
        f"{passing}/{len(cases)} retention variations observed",
    )


def configured_agent_cli_execution_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        exit_code, output = _invoke_configured_agent_cli(
            ["--config", case["config_path"], "--scenario", case["scenario"]]
        )
        if exit_code == 0 and case["expected_text"] in output:
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "configured_agent_cli_execution",
        score,
        1.0,
        f"{passing}/{len(cases)} CLI executions succeeded",
    )


def config_audit_provenance_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    with TemporaryDirectory() as temp_dir:
        for index, case in enumerate(cases):
            config = load_agent_config(Path(case["config_path"]))
            result = ConfiguredAgent(config).run_scenario(
                case["scenario"], Path(temp_dir) / f"case_{index}", approve_action=False
            )
            if (
                result.audit.config_hash is not None
                and result.audit.policy_reason is not None
                and result.audit.config_version == config.config_version
            ):
                passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "config_audit_provenance",
        score,
        1.0,
        f"{passing}/{len(cases)} audit records include config provenance",
    )


def holly_backward_compatibility_probe(cases: list[dict]) -> MetricResult:
    runners = {
        "project-companion": run_project_companion,
        "support-continuity": run_support_continuity,
        "operations-observer": lambda path: run_operations_observer(path, approved=False),
        "temporal-layering": run_temporal_layering,
        "persistent-identity": run_persistent_identity,
        "safety-gate": run_safety_gate,
    }
    passing = 0
    with TemporaryDirectory() as temp_dir:
        for index, case in enumerate(cases):
            result = runners[case["scenario"]](Path(temp_dir) / f"holly_{index}")
            telemetry = result.get("telemetry", {})
            actual = telemetry.get(case["field"])
            if actual == case["expected"]:
                passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "holly_backward_compatibility",
        score,
        1.0,
        f"{passing}/{len(cases)} Holly scenarios preserved expected outputs",
    )


def model_adapter_contract_normalization_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        adapter = create_provider_adapter(case.get("provider_id", "mock"), live=False)
        response = adapter.generate(
            ModelRequest(
                messages=[ModelMessage(role="user", content=case.get("prompt", "synthetic"))],
                scenario_id=case.get("scenario", "project-companion"),
            )
        )
        if response.provider_id == case.get("expected_provider_id", "mock") and response.text:
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "model_adapter_contract_normalization",
        score,
        1.0,
        f"{passing}/{len(cases)} provider responses normalized",
    )


def provider_capability_enforcement_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        config = get_provider_config(case["provider_id"])
        observed = getattr(config.capabilities, case["capability"])
        if observed is case["expected"]:
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "provider_capability_enforcement",
        score,
        1.0,
        f"{passing}/{len(cases)} declared capabilities enforced",
    )


def model_tool_proposal_safety_gate_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    with TemporaryDirectory() as temp_dir:
        for index, case in enumerate(cases):
            agent = ConfiguredAgent(load_agent_config(Path(case["config_path"])))
            result = agent.run_scenario(
                case["scenario"],
                Path(temp_dir) / f"provider_tool_{index}",
                provider_id="mock",
                provider_scenario="tool-proposal",
            )
            decisions = [decision.decision for decision in result.provider_safety_decisions]
            if (
                result.telemetry.get("provider_tool_executions") == 0
                and case["expected_decision"] in decisions
            ):
                passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "model_tool_proposal_safety_gate",
        score,
        1.0,
        f"{passing}/{len(cases)} proposals gated without execution",
    )


def provider_audit_secret_redaction_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        adapter = create_provider_adapter(case.get("provider_id", "openai"), live=False)
        redacted = adapter.sanitize_error(case["error"])
        if all(secret not in redacted for secret in case.get("must_not_contain", [])):
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "provider_audit_secret_redaction",
        score,
        1.0,
        f"{passing}/{len(cases)} provider errors redacted",
    )


def mock_provider_runtime_execution_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    with TemporaryDirectory() as temp_dir:
        for index, case in enumerate(cases):
            result = ConfiguredAgent(load_agent_config(Path(case["config_path"]))).run_scenario(
                case["scenario"], Path(temp_dir) / f"mock_runtime_{index}", provider_id="mock"
            )
            if (
                result.provider_response is not None
                and result.audit.provider is not None
                and result.telemetry.get("provider_id") == "mock"
            ):
                passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "mock_provider_runtime_execution",
        score,
        1.0,
        f"{passing}/{len(cases)} mock provider runtime executions passed",
    )


def provider_cli_mock_execution_probe(cases: list[dict]) -> MetricResult:
    passing = 0
    for case in cases:
        exit_code, output = _invoke_configured_agent_cli(
            [
                "--config",
                case["config_path"],
                "--scenario",
                case["scenario"],
                "--provider",
                "mock",
            ]
        )
        if exit_code == 0 and "provider_id=mock" in output:
            passing += 1
    score = passing / len(cases) if cases else 0.0
    return pass_at(
        "provider_cli_mock_execution",
        score,
        1.0,
        f"{passing}/{len(cases)} provider CLI mock executions passed",
    )


def _invoke_configured_agent_cli(arguments: list[str]) -> tuple[int, str]:
    original_argv = sys.argv[:]
    buffer = StringIO()
    try:
        sys.argv = ["centroid-agent", *arguments]
        with redirect_stdout(buffer):
            exit_code = configured_agent_cli_main()
    finally:
        sys.argv = original_argv
    return exit_code, buffer.getvalue()


def _holly_project_contradiction(events: list[Event], proposed_change: str) -> bool:
    constraints = [
        event.content.lower() for event in events if event.event_type == "project_constraint"
    ]
    proposal = proposed_change.lower()
    return any("only use approved site content" in constraint for constraint in constraints) and (
        "general model knowledge" in proposal
    )
