from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from core.identity import IdentityState
from core.memory import Event, MemoryStore
from core.priority import PrioritySignal, score_priority
from core.router import Router
from core.safety import SafetyPolicy
from core.self_model import SelfModelSnapshot
from core.temporal import latency_ms

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
