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


# ── Phase 4 expanded system-level module probes ─────────────────────────────

def _probe_result(name: str, ok: bool, details: str = "") -> MetricResult:
    return pass_at(name, 1.0 if ok else 0.0, 1.0, details)


def _probe_exception(name: str, exc: Exception) -> MetricResult:
    return pass_at(name, 0.0, 1.0, f"{type(exc).__name__}: {exc}")


def memory_append_tail_compat_probe(cases: list[dict]) -> MetricResult:
    try:
        with TemporaryDirectory() as temp_dir:
            store = MemoryStore(Path(temp_dir) / "events.jsonl")
            first = Event("observation", "first continuity event", "harness")
            second = Event("decision", "second continuity event", "harness")
            store.append(first)
            store.append(second)
            tail = store.tail(limit=2)
            ok = [event.content for event in tail] == [first.content, second.content]
            return _probe_result("memory_append_tail_compat", ok, f"tail={len(tail)}")
    except Exception as exc:
        return _probe_exception("memory_append_tail_compat", exc)


def memory_search_returns_results_probe(cases: list[dict]) -> MetricResult:
    try:
        with TemporaryDirectory() as temp_dir:
            store = MemoryStore(Path(temp_dir) / "events.jsonl")
            store.append(Event("observation", "safety router retained critical signal", "harness"))
            results = store.search("safety router", top_k=3)
            return _probe_result("memory_search_returns_results", bool(results), f"results={len(results)}")
    except Exception as exc:
        return _probe_exception("memory_search_returns_results", exc)


def memory_search_relevance_ordering_probe(cases: list[dict]) -> MetricResult:
    try:
        with TemporaryDirectory() as temp_dir:
            store = MemoryStore(Path(temp_dir) / "events.jsonl")
            store.append(Event("observation", "router coherence bridge signal", "harness"))
            store.append(Event("observation", "unrelated garden weather note", "harness"))
            results = store.search("router coherence bridge", top_k=2)
            ok = len(results) >= 2 and results[0].score >= results[-1].score
            return _probe_result("memory_search_relevance_ordering", ok, f"scores={[r.score for r in results]}")
    except Exception as exc:
        return _probe_exception("memory_search_relevance_ordering", exc)


def memory_pyramid_tier_assignment_probe(cases: list[dict]) -> MetricResult:
    try:
        with TemporaryDirectory() as temp_dir:
            store = MemoryStore(Path(temp_dir) / "events.jsonl")
            event = Event("decision", "critical decision checkpoint", "event_journal")
            store.append(event)
            counts = store.tier_counts()
            ok = counts.get("active", 0) >= 1
            return _probe_result("memory_pyramid_tier_assignment", ok, f"tiers={counts}")
    except Exception as exc:
        return _probe_exception("memory_pyramid_tier_assignment", exc)


def memory_compact_evicts_lowest_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.memory import TierCapacity
        with TemporaryDirectory() as temp_dir:
            store = MemoryStore(Path(temp_dir) / "events.jsonl", capacity=TierCapacity(active=1, working=0, long_term=0))
            low = Event("observation", "plain low salience note", "sensory_stream")
            high = Event("decision", "critical safety decision retained", "event_journal")
            store.append(low)
            store.append(high)
            retained, evicted = store.compact()
            ok = len(evicted) >= 1 and low.event_id in evicted and high.event_id in retained
            return _probe_result("memory_compact_evicts_lowest", ok, f"retained={len(retained)} evicted={len(evicted)}")
    except Exception as exc:
        return _probe_exception("memory_compact_evicts_lowest", exc)


def memory_index_rebuilds_on_init_probe(cases: list[dict]) -> MetricResult:
    try:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            MemoryStore(path).append(Event("observation", "rebuildable index token", "harness"))
            rebuilt = MemoryStore(path)
            results = rebuilt.search("rebuildable", top_k=1)
            ok = rebuilt.index_size == 1 and bool(results)
            return _probe_result("memory_index_rebuilds_on_init", ok, f"index_size={rebuilt.index_size}")
    except Exception as exc:
        return _probe_exception("memory_index_rebuilds_on_init", exc)


class _HarnessSource:
    def __init__(self, source_id: str, metrics: dict[str, float]) -> None:
        self.source_id = source_id
        self._metrics = metrics
    def read(self) -> dict[str, float]:
        return dict(self._metrics)
    def set_metrics(self, metrics: dict[str, float]) -> None:
        self._metrics = metrics


class _HarnessFaultySource:
    source_id = "faulty"
    def read(self) -> dict[str, float]:
        raise RuntimeError("synthetic failure")


def self_model_health_ratio_bounds_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.self_model import SelfModel
        with TemporaryDirectory() as temp_dir:
            sm = SelfModel(state_dir=temp_dir)
            sm.register_source(_HarnessSource("node", {"ok": 0.7}))
            sm.tick()
            ok = 0.0 <= sm.health_ratio <= 1.0
            return _probe_result("self_model_health_ratio_bounds", ok, f"ratio={sm.health_ratio:.4f}")
    except Exception as exc:
        return _probe_exception("self_model_health_ratio_bounds", exc)


def self_model_status_reflects_ratio_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.self_model import SelfModel
        with TemporaryDirectory() as temp_dir:
            sm = SelfModel(state_dir=temp_dir)
            sm.register_source(_HarnessSource("node", {"ok": 1.0}))
            sm.tick()
            ok = sm.health_ratio >= 1.0 and sm.status == "healthy"
            return _probe_result("self_model_status_reflects_ratio", ok, f"status={sm.status}")
    except Exception as exc:
        return _probe_exception("self_model_status_reflects_ratio", exc)


def self_model_tick_produces_snapshot_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.self_model import SelfModel
        with TemporaryDirectory() as temp_dir:
            sm = SelfModel(state_dir=temp_dir)
            sm.register_source(_HarnessSource("node", {"ok": 0.9}))
            sm.tick()
            ok = (Path(temp_dir) / "world_snapshot.json").exists()
            return _probe_result("self_model_tick_produces_snapshot", ok, "world_snapshot.json exists")
    except Exception as exc:
        return _probe_exception("self_model_tick_produces_snapshot", exc)


def self_model_anomaly_detection_fires_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.self_model import AnomalyDetector, AnomalyEvent
        detector = AnomalyDetector(warn_threshold=2.0, critical_threshold=10.0, min_samples=5)
        for value in [50.0, 51.0, 49.0, 52.0, 48.0]:
            detector.update("router", {"latency": value})
        events = detector.update("router", {"latency": 55.0})
        ok = bool(events) and isinstance(events[0], AnomalyEvent)
        return _probe_result("self_model_anomaly_detection_fires", ok, f"events={len(events)}")
    except Exception as exc:
        return _probe_exception("self_model_anomaly_detection_fires", exc)


def self_model_fault_tolerant_collect_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.self_model import SelfModel
        with TemporaryDirectory() as temp_dir:
            sm = SelfModel(state_dir=temp_dir)
            sm.register_source(_HarnessSource("healthy", {"ok": 1.0}))
            sm.register_source(_HarnessFaultySource())
            snap = sm.tick()
            ok = "healthy" in snap.node_health and "faulty" in snap.node_health
            return _probe_result("self_model_fault_tolerant_collect", ok, f"nodes={sorted(snap.node_health)}")
    except Exception as exc:
        return _probe_exception("self_model_fault_tolerant_collect", exc)


def self_model_backward_compat_no_sources_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.self_model import SelfModel
        sm = SelfModel()
        ok = sm.health_ratio == 0.0 and sm.status == "critical"
        return _probe_result("self_model_backward_compat_no_sources", ok, f"status={sm.status}")
    except Exception as exc:
        return _probe_exception("self_model_backward_compat_no_sources", exc)


def coherence_graph_loads_yaml_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.coherence import load_graph
        graph = load_graph("config/coherence_graph.yaml")
        ok = bool(graph.nodes) and bool(graph.edges)
        return _probe_result("coherence_graph_loads_yaml", ok, f"nodes={len(graph.nodes)} edges={len(graph.edges)}")
    except Exception as exc:
        return _probe_exception("coherence_graph_loads_yaml", exc)


def coherence_propagation_clamped_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.coherence import TopologicalPropagator, load_graph
        graph = load_graph("config/coherence_graph.yaml")
        values = TopologicalPropagator(graph).propagate({"memory": 2.0, "router": -1.0, "planner": 0.8, "safety": 1.0})
        ok = all(0.0 <= value <= 1.0 for value in values.values())
        return _probe_result("coherence_propagation_clamped", ok, f"values={values}")
    except Exception as exc:
        return _probe_exception("coherence_propagation_clamped", exc)


def coherence_suppresses_edge_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.coherence import CoherenceGraphDef, EdgeDef, NodeDef, TopologicalPropagator
        graph = CoherenceGraphDef([NodeDef("safety", ""), NodeDef("router", "")], [EdgeDef("safety", "router", "suppresses", 1.0)])
        prop = TopologicalPropagator(graph)
        high = prop.propagate({"safety": 1.0, "router": 0.8})["router"]
        low = prop.propagate({"safety": 0.0, "router": 0.8})["router"]
        ok = high < low
        return _probe_result("coherence_suppresses_edge", ok, f"high={high} low={low}")
    except Exception as exc:
        return _probe_exception("coherence_suppresses_edge", exc)


def coherence_index_scalar_bounds_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.coherence import CoherenceIndexCalculator, TopologicalPropagator, load_graph
        graph = load_graph("config/coherence_graph.yaml")
        prop = TopologicalPropagator(graph)
        report = CoherenceIndexCalculator(prop.inbound_weight_sum).compute(prop.propagate({}))
        ok = 0.0 <= report.coherence_index <= 1.0
        return _probe_result("coherence_index_scalar_bounds", ok, f"index={report.coherence_index:.4f}")
    except Exception as exc:
        return _probe_exception("coherence_index_scalar_bounds", exc)


def coherence_tick_writes_snapshot_probe(cases: list[dict]) -> MetricResult:
    try:
        import time
        from core.coherence import CoherenceGraph
        from core.self_model import SnapshotWriter, WorldSnapshot
        with TemporaryDirectory() as temp_dir:
            state = Path(temp_dir) / "state"
            writer = SnapshotWriter(state_dir=state)
            writer.write(WorldSnapshot(time.time(), {"memory": 0.9, "router": 0.5, "planner": 0.8, "safety": 0.95, "self_model": 0.85}, {}, 0.8, 0, None))
            cg = CoherenceGraph("config/coherence_graph.yaml", snapshot_path=state / "world_snapshot.json", snapshot_writer=writer)
            cg.tick()
            snap = writer.read_snapshot()
            ok = snap is not None and snap.coherence_index is not None and 0.0 <= snap.coherence_index <= 1.0
            return _probe_result("coherence_tick_writes_snapshot", ok, f"index={snap.coherence_index if snap else None}")
    except Exception as exc:
        return _probe_exception("coherence_tick_writes_snapshot", exc)


def coherence_simulate_no_disk_write_probe(cases: list[dict]) -> MetricResult:
    try:
        import time
        from core.coherence import CoherenceGraph, DoIntervention
        from core.self_model import SnapshotWriter, WorldSnapshot
        with TemporaryDirectory() as temp_dir:
            state = Path(temp_dir) / "state"
            writer = SnapshotWriter(state_dir=state)
            writer.write(WorldSnapshot(time.time(), {"memory": 0.9, "router": 0.5, "planner": 0.8, "safety": 0.95, "self_model": 0.85}, {}, 0.8, 0, None))
            path = state / "world_snapshot.json"
            before = path.read_text(encoding="utf-8")
            CoherenceGraph("config/coherence_graph.yaml", snapshot_path=path, snapshot_writer=writer).simulate(DoIntervention("safety", 0.0))
            after = path.read_text(encoding="utf-8")
            return _probe_result("coherence_simulate_no_disk_write", before == after, "snapshot unchanged")
    except Exception as exc:
        return _probe_exception("coherence_simulate_no_disk_write", exc)


def planner_forecast_three_horizons_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.planner import CalibrationStore, ForecastGenerator
        with TemporaryDirectory() as temp_dir:
            forecasts = ForecastGenerator(fields=["memory"]).generate({"memory": 0.9}, CalibrationStore(Path(temp_dir) / "cal.json"))
            ok = {f.horizon for f in forecasts} == {"short", "medium", "long"}
            return _probe_result("planner_forecast_three_horizons", ok, f"horizons={sorted(f.horizon for f in forecasts)}")
    except Exception as exc:
        return _probe_exception("planner_forecast_three_horizons", exc)


def planner_forecast_ids_unique_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.planner import CalibrationStore, ForecastGenerator
        with TemporaryDirectory() as temp_dir:
            cal = CalibrationStore(Path(temp_dir) / "cal.json")
            fg = ForecastGenerator(fields=["memory"])
            ids = [f.forecast_id for _ in range(2) for f in fg.generate({"memory": 0.5}, cal)]
            ok = len(ids) == len(set(ids)) == 6
            return _probe_result("planner_forecast_ids_unique", ok, f"ids={len(set(ids))}")
    except Exception as exc:
        return _probe_exception("planner_forecast_ids_unique", exc)


def planner_calibration_updates_mae_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.planner import CalibrationStore
        with TemporaryDirectory() as temp_dir:
            cal = CalibrationStore(Path(temp_dir) / "cal.json")
            cal.update("cpu", "short", 0.8, 0.6)
            before = cal.get("cpu", "short").mae
            cal.update("cpu", "short", 0.5, 0.5)
            after = cal.get("cpu", "short").mae
            return _probe_result("planner_calibration_updates_mae", after < before, f"before={before} after={after}")
    except Exception as exc:
        return _probe_exception("planner_calibration_updates_mae", exc)


def planner_calibration_persists_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.planner import CalibrationStore
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state" / "calibration.json"
            cal = CalibrationStore(path)
            cal.update("cpu", "short", 0.5, 0.5)
            return _probe_result("planner_calibration_persists", path.exists(), str(path))
    except Exception as exc:
        return _probe_exception("planner_calibration_persists", exc)


def planner_thread_lifecycle_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.planner import PlanStep, PlanTree
        with TemporaryDirectory() as temp_dir:
            tree = PlanTree(state_path=Path(temp_dir) / "plan_tree.json")
            thread = tree.add_thread("goal", [PlanStep("step")], 0.8)
            active = thread.status == "active"
            tree.complete(thread.thread_id)
            ok = active and thread.status == "completed"
            return _probe_result("planner_thread_lifecycle", ok, f"status={thread.status}")
    except Exception as exc:
        return _probe_exception("planner_thread_lifecycle", exc)


def planner_feedback_resolves_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.planner import CalibrationStore, ForecastFeedbackLoop, ForecastGenerator, PlanTree
        with TemporaryDirectory() as temp_dir:
            cal = CalibrationStore(Path(temp_dir) / "cal.json")
            loop = ForecastFeedbackLoop(cal, PlanTree(state_path=Path(temp_dir) / "plan_tree.json"))
            forecast = [f for f in ForecastGenerator(fields=["cpu"]).generate({"cpu": 0.8}, cal) if f.horizon == "short"][0]
            loop.register(forecast)
            results = loop.resolve({"cpu": 0.75})
            ok = len(results) == 1 and results[0].forecast_id == forecast.forecast_id
            return _probe_result("planner_feedback_resolves", ok, f"resolved={len(results)}")
    except Exception as exc:
        return _probe_exception("planner_feedback_resolves", exc)


def _write_snapshot(path: Path, snapshot: dict | None = None) -> None:
    payload = snapshot or {"timestamp": 1.0, "node_health": {"router": 0.8, "safety": 0.9}, "node_trends": {}, "system_health_ratio": 0.85, "anomaly_count": 0, "coherence_index": 0.8}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def simulation_fork_isolated_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.simulation import TwinBuffer
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "world_snapshot.json"
            _write_snapshot(path)
            buffer = TwinBuffer(path)
            twin = buffer.fork()
            twin.snapshot["node_health"]["router"] = 0.0
            ok = buffer.actual_snapshot()["node_health"]["router"] == 0.8
            return _probe_result("simulation_fork_isolated", ok, "actual snapshot unchanged")
    except Exception as exc:
        return _probe_exception("simulation_fork_isolated", exc)


def simulation_intervention_applies_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.simulation import Intervention, InterventionApplicator, TwinBuffer
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "world_snapshot.json"
            _write_snapshot(path)
            twin = TwinBuffer(path).fork()
            InterventionApplicator().apply(twin, Intervention("route", "node_health.router", 0.2, "set router"))
            ok = twin.snapshot["node_health"]["router"] == 0.2
            return _probe_result("simulation_intervention_applies", ok, "node_health.router mutated")
    except Exception as exc:
        return _probe_exception("simulation_intervention_applies", exc)


def simulation_divergence_zero_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.simulation import DivergenceCalculator
        calc = DivergenceCalculator()
        calc.sample("fork", {"a": 1.0, "b": 0.5}, {"a": 1.0, "b": 0.5}, 0)
        metric = calc.compute("fork")
        return _probe_result("simulation_divergence_zero", metric.weighted_divergence == 0.0, f"D={metric.weighted_divergence}")
    except Exception as exc:
        return _probe_exception("simulation_divergence_zero", exc)


def simulation_preflight_escalates_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.simulation import DivergenceCalculator, Intervention, InterventionApplicator, SafetyPreflight, TwinBuffer
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "world_snapshot.json"
            _write_snapshot(path, {"timestamp": 1.0, "score": 0.0})
            preflight = SafetyPreflight(TwinBuffer(path), InterventionApplicator(), DivergenceCalculator(), divergence_threshold=0.25, simulation_cycles=1)
            verdict = preflight.evaluate(Intervention("mutate", "score", 1.0, "large change"), "allow")
            ok = verdict.escalated and verdict.final_decision == "hold"
            return _probe_result("simulation_preflight_escalates", ok, f"decision={verdict.final_decision} D={verdict.divergence}")
    except Exception as exc:
        return _probe_exception("simulation_preflight_escalates", exc)


def simulation_preflight_no_disk_write_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.simulation import DivergenceCalculator, Intervention, InterventionApplicator, SafetyPreflight, TwinBuffer
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "world_snapshot.json"
            _write_snapshot(path, {"timestamp": 1.0, "score": 0.0})
            before = path.read_text(encoding="utf-8")
            SafetyPreflight(TwinBuffer(path), InterventionApplicator(), DivergenceCalculator(), simulation_cycles=1).evaluate(Intervention("mutate", "score", 0.1, "small change"), "allow")
            after = path.read_text(encoding="utf-8")
            return _probe_result("simulation_preflight_no_disk_write", before == after, "snapshot unchanged")
    except Exception as exc:
        return _probe_exception("simulation_preflight_no_disk_write", exc)


def sensory_code_encoder_extracts_probe(cases: list[dict]) -> MetricResult:
    try:
        from nodes.sensory_node import CodeEncoder, PerceivedText
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "module.py"
            path.write_text('"""doc"""\n\ndef sample():\n    """fn"""\n    return 1\n', encoding="utf-8")
            perceived = CodeEncoder().encode_file(path)
            ok = isinstance(perceived, PerceivedText) and "def sample" in perceived.content
            return _probe_result("sensory_code_encoder_extracts", ok, "content extracted")
    except Exception as exc:
        return _probe_exception("sensory_code_encoder_extracts", exc)


def sensory_telemetry_qualifiers_probe(cases: list[dict]) -> MetricResult:
    try:
        from nodes.sensory_node import TelemetryEncoder
        content = TelemetryEncoder().encode("node", {"load": 0.9}).content
        return _probe_result("sensory_telemetry_qualifiers", "(high)" in content, content)
    except Exception as exc:
        return _probe_exception("sensory_telemetry_qualifiers", exc)


def sensory_encoder_truncates_probe(cases: list[dict]) -> MetricResult:
    try:
        from nodes.sensory_node import SensoryEncoder
        perceived = SensoryEncoder().encode({"text": "x" * 600}, "obs")
        ok = len(perceived.content) == 512 and perceived.content.endswith("...[truncated]")
        return _probe_result("sensory_encoder_truncates", ok, f"len={len(perceived.content)}")
    except Exception as exc:
        return _probe_exception("sensory_encoder_truncates", exc)


def sensory_projector_similarity_self_probe(cases: list[dict]) -> MetricResult:
    try:
        import time
        from nodes.sensory_node import LatentProjector, PerceivedText
        projector = LatentProjector()
        perceived = PerceivedText("code", "shared signal", "module.py", time.time())
        projector.add(perceived)
        score = projector.similarity(perceived, perceived)
        return _probe_result("sensory_projector_similarity_self", score == 1.0, f"score={score}")
    except Exception as exc:
        return _probe_exception("sensory_projector_similarity_self", exc)


def sensory_pipeline_startup_scan_probe(cases: list[dict]) -> MetricResult:
    try:
        from nodes.sensory_node import SensoryPipeline
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "core"
            root.mkdir()
            (root / "module.py").write_text("def sample():\n    return 1\n", encoding="utf-8")
            results = SensoryPipeline(core_root=root).run_startup_scan()
            return _probe_result("sensory_pipeline_startup_scan", bool(results), f"results={len(results)}")
    except Exception as exc:
        return _probe_exception("sensory_pipeline_startup_scan", exc)


def _fusion_graph():
    import time
    from core.fusion import ConceptGraphBuilder
    from nodes.sensory_node import PerceivedText
    return ConceptGraphBuilder().build([
        PerceivedText("code", "alpha bridge shared signal", "module_a", time.time()),
        PerceivedText("code", "bridge shared beta signal", "module_b", time.time()),
    ])


def fusion_concept_graph_builds_probe(cases: list[dict]) -> MetricResult:
    try:
        graph = _fusion_graph()
        return _probe_result("fusion_concept_graph_builds", bool(graph.nodes), f"nodes={len(graph.nodes)}")
    except Exception as exc:
        return _probe_exception("fusion_concept_graph_builds", exc)


def fusion_stopwords_filtered_probe(cases: list[dict]) -> MetricResult:
    try:
        import time
        from core.fusion import ConceptGraphBuilder
        from nodes.sensory_node import PerceivedText
        graph = ConceptGraphBuilder().build([PerceivedText("code", "the and useful useful", "module_a", time.time()), PerceivedText("code", "useful", "module_b", time.time())])
        ok = "the" not in graph.nodes and "and" not in graph.nodes
        return _probe_result("fusion_stopwords_filtered", ok, f"nodes={sorted(graph.nodes)}")
    except Exception as exc:
        return _probe_exception("fusion_stopwords_filtered", exc)


def fusion_bridge_detector_finds_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.fusion import BridgeDetector
        candidates = BridgeDetector().detect(_fusion_graph())
        return _probe_result("fusion_bridge_detector_finds", bool(candidates), f"candidates={len(candidates)}")
    except Exception as exc:
        return _probe_exception("fusion_bridge_detector_finds", exc)


def fusion_bridge_score_bounds_probe(cases: list[dict]) -> MetricResult:
    try:
        from core.fusion import BridgeDetector
        candidates = BridgeDetector().detect(_fusion_graph())
        ok = bool(candidates) and all(0.0 <= candidate.bridge_score <= 1.0 for candidate in candidates)
        return _probe_result("fusion_bridge_score_bounds", ok, f"candidates={len(candidates)}")
    except Exception as exc:
        return _probe_exception("fusion_bridge_score_bounds", exc)


def fusion_synthesis_fallback_probe(cases: list[dict]) -> MetricResult:
    try:
        import os
        from core.fusion import BridgeDetector, BridgeSynthesizer, SynthesisResult
        old_ollama = os.environ.pop("OLLAMA_HOST", None)
        old_centroid = os.environ.pop("CENTROID_OLLAMA_URL", None)
        try:
            graph = _fusion_graph()
            bridge = BridgeDetector().detect(graph)[0]
            result = BridgeSynthesizer().synthesize(bridge, graph)
            ok = isinstance(result, SynthesisResult) and result.llm_available is False and result.synthesis_text
            return _probe_result("fusion_synthesis_fallback", ok, f"llm={result.llm_available}")
        finally:
            if old_ollama is not None:
                os.environ["OLLAMA_HOST"] = old_ollama
            if old_centroid is not None:
                os.environ["CENTROID_OLLAMA_URL"] = old_centroid
    except Exception as exc:
        return _probe_exception("fusion_synthesis_fallback", exc)
