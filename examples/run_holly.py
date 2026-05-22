from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.agent_config import AgentConfig, load_agent_config
from core.evaluation.probes import reconciliation_probe
from core.identity import IdentityState
from core.memory import Event, MemoryStore
from core.priority import PrioritySignal, score_priority
from core.router import Router
from core.safety import SafetyPolicy

REPO_ROOT = Path(__file__).resolve().parents[1]
HOLLY_CONFIG_DIR = Path("configs") / "holly"

CONFIG_BY_SCENARIO = {
    "project-companion": HOLLY_CONFIG_DIR / "project_companion.json",
    "support-continuity": HOLLY_CONFIG_DIR / "support_continuity.json",
    "operations-observer": HOLLY_CONFIG_DIR / "operations_observer.json",
    "temporal-layering": HOLLY_CONFIG_DIR / "operations_observer.json",
    "persistent-identity": HOLLY_CONFIG_DIR / "base.json",
    "safety-gate": HOLLY_CONFIG_DIR / "operations_observer.json",
}


def load_holly_config(scenario: str = "persistent-identity") -> AgentConfig:
    if scenario not in CONFIG_BY_SCENARIO:
        raise ValueError(f"unknown Holly scenario: {scenario}")
    return load_agent_config(CONFIG_BY_SCENARIO[scenario])


def run_project_companion(state_dir: Path) -> dict[str, Any]:
    config = load_holly_config("project-companion")
    store = MemoryStore(state_dir / "project_companion.jsonl")
    identity = config.to_identity_state()

    _append_event(
        store,
        "project_goal",
        "Build a website for a fictional hatchery supplier.",
        {"provenance": "synthetic_session_1", "state_ref": "project:goal"},
    )
    _append_event(
        store,
        "project_decision",
        "Checkout integration will use PayPal.",
        {"provenance": "synthetic_session_1", "state_ref": "project:checkout"},
    )
    _append_event(
        store,
        "project_constraint",
        "Customer-facing chatbot answers must only use approved site content.",
        {"provenance": "synthetic_session_1", "state_ref": "project:chatbot"},
    )

    restored_events = store.tail(limit=3)
    proposed_change = "Allow chatbot answers from general model knowledge."
    contradictions = _detect_project_contradictions(restored_events, proposed_change)
    restored_identity = IdentityState(
        agent_id=identity.agent_id,
        version=identity.version,
        goals=list(identity.goals),
        invariants=list(identity.invariants),
    )
    drift = identity.drift_score(restored_identity)

    return {
        "scenario": "project-companion",
        "config": config,
        "friendly": (
            "Holly: I restored the project state. Your active constraint is that "
            "customer-facing answers must be grounded in approved site content."
        ),
        "telemetry": {
            "agent_id": config.agent_id,
            "memory_events_restored": len(restored_events),
            "identity_drift": drift,
            "approval_required": False,
            "contradictions_detected": len(contradictions),
            "next_step": "keep chatbot answers tied to approved content sources",
        },
        "contradictions": contradictions,
    }


def run_support_continuity(state_dir: Path) -> dict[str, Any]:
    config = load_holly_config("support-continuity")
    store = MemoryStore(state_dir / "support_continuity.jsonl")

    _append_event(
        store,
        "support_issue_opened",
        "Fictional customer reports incubator controller error E17 after power loss.",
        {"provenance": "synthetic_ticket_1001", "case_id": "case-1001"},
    )
    _append_event(
        store,
        "support_handoff_note",
        "Customer has hatch date pressure; request status updates before shipment promises.",
        {"provenance": "synthetic_agent_note", "case_id": "case-1001"},
    )

    priority = score_priority(PrioritySignal(urgency=0.8, risk=0.7, user_value=0.9, stability=0.4))
    route = Router().route(priority=priority, mutates_state=False)
    unsupported_response = "promise a replacement controller ships today"
    decision = SafetyPolicy().evaluate(unsupported_response, mode="act", confirmed=False)
    handoff_events = store.tail(limit=2)

    return {
        "scenario": "support-continuity",
        "config": config,
        "friendly": (
            "Holly: I restored the support handoff. The case is urgent, but I will "
            "escalate before making unsupported replacement or shipment promises."
        ),
        "telemetry": {
            "agent_id": config.agent_id,
            "case_id": "case-1001",
            "memory_events_restored": len(handoff_events),
            "priority": priority,
            "route": route.node,
            "approval_required": decision.requires_approval,
            "unsupported_response_blocked": not decision.allowed,
        },
        "handoff_note": "status update needed before replacement promise",
    }


def run_operations_observer(state_dir: Path, *, approved: bool = False) -> dict[str, Any]:
    config = load_holly_config("operations-observer")
    store = MemoryStore(state_dir / "operations_observer.jsonl")

    telemetry = {
        "service": "checkout-worker",
        "status": "unhealthy",
        "error_rate": "0.42",
        "log_signal": "repeated synthetic connection failures",
    }
    _append_event(
        store,
        "synthetic_telemetry",
        "checkout-worker unhealthy with repeated synthetic connection failures.",
        {"provenance": "synthetic_ops_fixture", "service": telemetry["service"]},
    )
    priority = score_priority(PrioritySignal(urgency=0.9, risk=0.8, user_value=0.7, stability=0.2))
    observation_route = Router().route(priority=priority, mutates_state=False)
    proposed_action = "restart service checkout-worker"
    safety = SafetyPolicy().evaluate(proposed_action, mode="act", confirmed=approved)
    audit = {
        "service": telemetry["service"],
        "proposed_action": proposed_action,
        "allowed": safety.allowed,
        "requires_approval": safety.requires_approval,
        "executed": safety.allowed and approved,
        "reasons": safety.reasons,
    }

    return {
        "scenario": "operations-observer",
        "config": config,
        "friendly": (
            "Holly: I found an unhealthy synthetic service and propose a restart, "
            "but the operation remains blocked until approval is recorded."
        ),
        "telemetry": {
            "agent_id": config.agent_id,
            "service": telemetry["service"],
            "risk": "elevated",
            "priority": priority,
            "route": observation_route.node,
            "approval_required": safety.requires_approval,
            "action_executed": audit["executed"],
        },
        "audit": audit,
    }


def run_temporal_layering(state_dir: Path) -> dict[str, Any]:
    config = load_holly_config("temporal-layering")
    store = MemoryStore(state_dir / "temporal_layering.jsonl")
    _append_event(
        store,
        "temporal_observation",
        "Potential service instability detected in synthetic telemetry.",
        {"provenance": "synthetic_ops_fixture", "service": "checkout-worker"},
    )

    trace = {
        "reflex_response_ms": 31,
        "deliberative_response_ms": 4200,
        "state_reconciliation_ms": 4388,
        "max_reflex_ms": 100,
        "max_deliberative_ms": 5000,
        "max_reconciliation_ms": 6000,
    }
    result = reconciliation_probe([trace])

    return {
        "scenario": "temporal-layering",
        "config": config,
        "friendly": (
            "Holly reflex: Potential service instability detected. No action taken.\n"
            "Holly deliberation: Repeated failures make a restart proposal reasonable, "
            "but approval is required."
        ),
        "telemetry": {
            "agent_id": config.agent_id,
            "reflex_response_ms": trace["reflex_response_ms"],
            "deliberation_response_ms": trace["deliberative_response_ms"],
            "reconciliation_delay_ms": trace["state_reconciliation_ms"],
            "reconciliation_passed": result.passed,
        },
    }


def run_persistent_identity(state_dir: Path) -> dict[str, Any]:
    config = load_holly_config("persistent-identity")
    store = MemoryStore(state_dir / "persistent_identity.jsonl")
    session_1 = config.to_identity_state()
    session_2 = session_1.evolve(goals=session_1.goals + ["restore public demo state"])
    _append_event(
        store,
        "identity_checkpoint",
        "Holly reference identity state checkpoint.",
        {"provenance": "synthetic_identity_session", "version": str(session_2.version)},
    )
    restored = IdentityState(
        agent_id=session_2.agent_id,
        version=session_2.version,
        goals=list(session_2.goals),
        invariants=list(session_2.invariants),
    )
    drift = session_2.drift_score(restored)

    return {
        "scenario": "persistent-identity",
        "config": config,
        "friendly": (
            "Holly: I loaded my reference configuration and restored versioned "
            "continuity state from a synthetic checkpoint."
        ),
        "telemetry": {
            "agent_id": config.agent_id,
            "display_name": config.display_name,
            "session_1_version": session_1.version,
            "session_2_version": session_2.version,
            "restored_version": restored.version,
            "memory_events_restored": len(store.tail(limit=1)),
            "identity_drift": drift,
        },
    }


def run_safety_gate(state_dir: Path) -> dict[str, Any]:
    result = run_operations_observer(state_dir, approved=False)
    result["scenario"] = "safety-gate"
    result["friendly"] = (
        "Holly: I can propose the restart, but I did not execute it because the "
        "approval decision is still pending."
    )
    result["audit"]["approval_decision"] = "pending"
    return result


def print_result(result: dict[str, Any]) -> None:
    print(f"[scenario] {result['scenario']}")
    print(result["friendly"])
    print()
    print("[continuity]")
    for key, value in result["telemetry"].items():
        print(f"{key}={_format_value(value)}")
    if result.get("contradictions"):
        print()
        print("[contradictions]")
        for item in result["contradictions"]:
            print(item)
    if result.get("audit"):
        print()
        print("[audit]")
        for key, value in result["audit"].items():
            print(f"{key}={_format_value(value)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Holly reference scenarios.")
    parser.add_argument(
        "--scenario",
        choices=tuple(CONFIG_BY_SCENARIO.keys()),
        default="project-companion",
    )
    parser.add_argument("--state-dir", type=Path, default=Path("runtime_state") / "holly")
    parser.add_argument("--approve-action", action="store_true")
    args = parser.parse_args()

    args.state_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = args.state_dir / args.scenario
    scenario_dir.mkdir(parents=True, exist_ok=True)

    runners = {
        "project-companion": run_project_companion,
        "support-continuity": run_support_continuity,
        "operations-observer": lambda path: run_operations_observer(
            path, approved=args.approve_action
        ),
        "temporal-layering": run_temporal_layering,
        "persistent-identity": run_persistent_identity,
        "safety-gate": run_safety_gate,
    }
    result = runners[args.scenario](scenario_dir)
    print_result(result)
    return 0


def _append_event(
    store: MemoryStore, event_type: str, content: str, metadata: dict[str, str]
) -> None:
    store.append(
        Event(event_type=event_type, content=content, source="holly_demo", metadata=metadata)
    )


def _detect_project_contradictions(events: list[Event], proposed_change: str) -> list[str]:
    constraints = [
        event.content.lower() for event in events if event.event_type == "project_constraint"
    ]
    proposal = proposed_change.lower()
    if any("only use approved site content" in constraint for constraint in constraints):
        if "general model knowledge" in proposal:
            return [
                "proposed chatbot source policy conflicts with approved-content-only constraint"
            ]
    return []


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
