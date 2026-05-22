from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.agent_config import AgentConfig, load_agent_config
from core.identity import IdentityState
from core.memory import Event
from core.priority import PrioritySignal

from .audit import AuditRecord, build_audit_record, config_hash
from .configured_memory import ConfiguredMemoryManager, MemoryRetentionResult
from .configured_priority import ConfiguredPriorityScorer
from .configured_safety import ActionRequest, ConfiguredSafetyPolicy, SafetyDecision

AVAILABLE_SCENARIOS = (
    "project-companion",
    "support-continuity",
    "operations-observer",
    "temporal-layering",
    "persistent-identity",
    "safety-gate",
)


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    config: AgentConfig
    priority: float
    route: str
    route_reason: str
    friendly: str
    telemetry: dict[str, Any]
    memory: MemoryRetentionResult
    audit: AuditRecord
    safety: SafetyDecision
    contradictions: list[str] = field(default_factory=list)


class ConfiguredAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.config_digest = config_hash(config)
        self.priority = ConfiguredPriorityScorer(config.priority_policy)
        self.safety = ConfiguredSafetyPolicy(config.safety_policy, config_hash=self.config_digest)
        self.memory = ConfiguredMemoryManager(config.memory_policy)

    def run_scenario(
        self, scenario: str, state_dir: Path, *, approve_action: bool = False
    ) -> ScenarioResult:
        if scenario == "project-companion":
            return self._run_project_companion(state_dir)
        if scenario == "support-continuity":
            return self._run_support_continuity(state_dir)
        if scenario == "operations-observer":
            return self._run_operations_observer(state_dir, approve_action=approve_action)
        if scenario == "temporal-layering":
            return self._run_temporal_layering(state_dir)
        if scenario == "persistent-identity":
            return self._run_persistent_identity(state_dir)
        if scenario == "safety-gate":
            result = self._run_operations_observer(state_dir, approve_action=False)
            return ScenarioResult(
                scenario="safety-gate",
                config=result.config,
                priority=result.priority,
                route=result.route,
                route_reason=result.route_reason,
                friendly=(
                    f"{self.config.display_name}: I can propose the restart, but I did not "
                    "execute it because the approval decision is still pending."
                ),
                telemetry=result.telemetry,
                memory=result.memory,
                audit=result.audit,
                safety=result.safety,
            )
        raise ValueError(f"unknown scenario: {scenario}")

    def comparison_case(self) -> dict[str, Any]:
        signal = PrioritySignal(urgency=0.65, risk=0.75, user_value=0.45, stability=0.55)
        priority = self.priority.route(signal, mutates_state=False)
        decision = self.safety.evaluate(
            ActionRequest(
                action_type="restart_service",
                resource="synthetic-service",
                intended_effect="propose a restart after repeated synthetic failures",
                risk_level="medium",
                reversible=True,
                requested_by="comparison-demo",
                config_id=self.config.agent_id,
                mode="plan",
            )
        )
        events = [
            Event(
                event_type="comparison_checkpoint",
                content="same synthetic continuity checkpoint for comparison",
                source="config_comparison",
                metadata={"memory_kind": "checkpoint", "provenance": "comparison_fixture"},
            ),
            Event(
                event_type="audit_event",
                content="same synthetic audit record for comparison",
                source="config_comparison",
                metadata={"memory_kind": "audit", "provenance": "comparison_fixture"},
            ),
            Event(
                event_type="comparison_summary_source",
                content="same synthetic task summary source for comparison",
                source="config_comparison",
                metadata={"memory_kind": "session", "provenance": "comparison_fixture"},
            ),
        ]
        memory = self.memory.retain(events)
        return {
            "display_name": self.config.display_name,
            "agent_id": self.config.agent_id,
            "route": priority.route.node,
            "priority": priority.score,
            "memory_write": memory.primary_record,
            "approval_required": decision.approval_required,
            "safety_decision": decision.decision,
        }

    def _run_project_companion(self, state_dir: Path) -> ScenarioResult:
        identity = self.config.to_identity_state()
        events = [
            self._event(
                "project_goal",
                "Build a website for a fictional hatchery supplier.",
                {
                    "provenance": "synthetic_session_1",
                    "state_ref": "project:goal",
                    "memory_kind": "checkpoint",
                },
            ),
            self._event(
                "project_decision",
                "Checkout integration will use PayPal.",
                {
                    "provenance": "synthetic_session_1",
                    "state_ref": "project:checkout",
                    "memory_kind": "checkpoint",
                },
            ),
            self._event(
                "project_constraint",
                "Customer-facing chatbot answers must only use approved site content.",
                {
                    "provenance": "synthetic_session_1",
                    "state_ref": "project:chatbot",
                    "memory_kind": "checkpoint",
                },
            ),
        ]
        memory = self.memory.persist(state_dir / "project_companion.jsonl", events)
        priority = self.priority.route(
            PrioritySignal(urgency=0.35, risk=0.20, user_value=0.80, stability=0.85),
            mutates_state=False,
        )
        proposed_change = "Allow chatbot answers from general model knowledge."
        contradictions = self._detect_project_contradictions(
            memory.retained_events, proposed_change
        )
        restored_identity = IdentityState(
            agent_id=identity.agent_id,
            version=identity.version,
            goals=list(identity.goals),
            invariants=list(identity.invariants),
        )
        safety = self.safety.evaluate(
            ActionRequest(
                action_type="review_project_state",
                resource="project-companion",
                intended_effect="restore continuity and review contradictions",
                risk_level="low",
                reversible=True,
                requested_by="scenario_runner",
                config_id=self.config.agent_id,
            )
        )
        audit = self._audit(
            "project-companion", priority.score, priority.route.node, safety, memory
        )
        return ScenarioResult(
            scenario="project-companion",
            config=self.config,
            priority=priority.score,
            route=priority.route.node,
            route_reason=priority.route.reason,
            friendly=(
                f"{self.config.display_name}: I restored the project state. Your active "
                "constraint is that customer-facing answers must be grounded in approved "
                "site content."
            ),
            telemetry={
                "agent_id": self.config.agent_id,
                "memory_events_restored": len(memory.retained_events),
                "identity_drift": identity.drift_score(restored_identity),
                "approval_required": safety.approval_required,
                "contradictions_detected": len(contradictions),
                "next_step": "keep chatbot answers tied to approved content sources",
                "route": priority.route.node,
                "config_hash": self.config_digest[:12],
            },
            memory=memory,
            audit=audit,
            safety=safety,
            contradictions=contradictions,
        )

    def _run_support_continuity(self, state_dir: Path) -> ScenarioResult:
        events = [
            self._event(
                "support_issue_opened",
                "Fictional customer reports incubator controller error E17 after power loss.",
                {
                    "provenance": "synthetic_ticket_1001",
                    "case_id": "case-1001",
                    "customer_id": "fictional-customer-17",
                    "memory_kind": "session",
                },
            ),
            self._event(
                "support_handoff_note",
                (
                    "Customer has hatch date pressure; request status updates before "
                    "shipment promises."
                ),
                {
                    "provenance": "synthetic_agent_note",
                    "case_id": "case-1001",
                    "customer_id": "fictional-customer-17",
                    "memory_kind": "session",
                },
            ),
        ]
        memory = self.memory.persist(state_dir / "support_continuity.jsonl", events)
        priority = self.priority.route(
            PrioritySignal(urgency=0.80, risk=0.70, user_value=0.90, stability=0.40),
            mutates_state=False,
        )
        safety = self.safety.evaluate(
            ActionRequest(
                action_type="make_support_promise",
                resource="case-1001",
                intended_effect="promise a replacement controller ships today",
                risk_level="medium",
                reversible=False,
                requested_by="scenario_runner",
                config_id=self.config.agent_id,
                mode="act",
            )
        )
        audit = self._audit(
            "support-continuity", priority.score, priority.route.node, safety, memory
        )
        return ScenarioResult(
            scenario="support-continuity",
            config=self.config,
            priority=priority.score,
            route=priority.route.node,
            route_reason=priority.route.reason,
            friendly=(
                f"{self.config.display_name}: I restored the support handoff. The case is urgent, "
                "but I will escalate before making unsupported replacement or shipment promises."
            ),
            telemetry={
                "agent_id": self.config.agent_id,
                "case_id": "case-1001",
                "memory_events_restored": len(memory.retained_events),
                "priority": priority.score,
                "route": priority.route.node,
                "approval_required": safety.approval_required,
                "unsupported_response_blocked": safety.decision != "allow",
                "config_hash": self.config_digest[:12],
            },
            memory=memory,
            audit=audit,
            safety=safety,
        )

    def _run_operations_observer(self, state_dir: Path, *, approve_action: bool) -> ScenarioResult:
        events = [
            self._event(
                "synthetic_telemetry",
                "checkout-worker unhealthy with repeated synthetic connection failures.",
                {
                    "provenance": "synthetic_ops_fixture",
                    "service": "checkout-worker",
                    "memory_kind": "session",
                },
            ),
            self._event(
                "audit_event",
                "proposed restart for checkout-worker after synthetic telemetry review.",
                {
                    "provenance": "synthetic_ops_fixture",
                    "service": "checkout-worker",
                    "memory_kind": "audit",
                },
            ),
        ]
        memory = self.memory.persist(state_dir / "operations_observer.jsonl", events)
        priority = self.priority.route(
            PrioritySignal(urgency=0.90, risk=0.80, user_value=0.70, stability=0.20),
            mutates_state=False,
        )
        safety = self.safety.evaluate(
            ActionRequest(
                action_type="restart_service",
                resource="checkout-worker",
                intended_effect="restart service checkout-worker",
                risk_level="high",
                reversible=True,
                requested_by="scenario_runner",
                config_id=self.config.agent_id,
                mode="act",
                confirmed=approve_action,
                mutates_state=True,
            )
        )
        audit = self._audit(
            "operations-observer", priority.score, priority.route.node, safety, memory
        )
        return ScenarioResult(
            scenario="operations-observer",
            config=self.config,
            priority=priority.score,
            route=priority.route.node,
            route_reason=priority.route.reason,
            friendly=(
                f"{self.config.display_name}: I found an unhealthy synthetic service and "
                "propose a restart, but the operation remains blocked until approval is recorded."
            ),
            telemetry={
                "agent_id": self.config.agent_id,
                "service": "checkout-worker",
                "risk": "elevated",
                "priority": priority.score,
                "route": priority.route.node,
                "approval_required": safety.approval_required,
                "action_executed": safety.allowed and approve_action,
                "memory_write": memory.primary_record,
                "config_hash": self.config_digest[:12],
            },
            memory=memory,
            audit=audit,
            safety=safety,
        )

    def _run_temporal_layering(self, state_dir: Path) -> ScenarioResult:
        memory = self.memory.persist(
            state_dir / "temporal_layering.jsonl",
            [
                self._event(
                    "temporal_observation",
                    "Potential service instability detected in synthetic telemetry.",
                    {"provenance": "synthetic_ops_fixture", "memory_kind": "audit"},
                )
            ],
        )
        priority = self.priority.route(
            PrioritySignal(urgency=0.70, risk=0.70, user_value=0.50, stability=0.30),
            mutates_state=False,
        )
        trace = {
            "reflex_response_ms": 31,
            "deliberative_response_ms": 4200,
            "state_reconciliation_ms": 4388,
            "max_reflex_ms": 100,
            "max_deliberative_ms": 5000,
            "max_reconciliation_ms": 6000,
        }
        reconciliation_passed = (
            trace["reflex_response_ms"] <= trace["max_reflex_ms"]
            and trace["deliberative_response_ms"] <= trace["max_deliberative_ms"]
            and trace["state_reconciliation_ms"] <= trace["max_reconciliation_ms"]
            and trace["reflex_response_ms"]
            <= trace["deliberative_response_ms"]
            <= trace["state_reconciliation_ms"]
        )
        safety = self.safety.evaluate(
            ActionRequest(
                action_type="review_temporal_trace",
                resource="temporal-layering",
                intended_effect="review timing traces",
                risk_level="low",
                reversible=True,
                requested_by="scenario_runner",
                config_id=self.config.agent_id,
            )
        )
        audit = self._audit(
            "temporal-layering", priority.score, priority.route.node, safety, memory
        )
        return ScenarioResult(
            scenario="temporal-layering",
            config=self.config,
            priority=priority.score,
            route=priority.route.node,
            route_reason=priority.route.reason,
            friendly=(
                f"{self.config.display_name} reflex: Potential service instability detected. "
                "No action taken.\n"
                f"{self.config.display_name} deliberation: Repeated failures make a restart "
                "proposal reasonable, but approval is required."
            ),
            telemetry={
                "agent_id": self.config.agent_id,
                "reflex_response_ms": trace["reflex_response_ms"],
                "deliberation_response_ms": trace["deliberative_response_ms"],
                "reconciliation_delay_ms": trace["state_reconciliation_ms"],
                "reconciliation_passed": reconciliation_passed,
                "route": priority.route.node,
                "config_hash": self.config_digest[:12],
            },
            memory=memory,
            audit=audit,
            safety=safety,
        )

    def _run_persistent_identity(self, state_dir: Path) -> ScenarioResult:
        session_1 = self.config.to_identity_state()
        session_2 = session_1.evolve(goals=session_1.goals + ["restore public demo state"])
        events = [
            self._event(
                "identity_checkpoint",
                "Reference identity state checkpoint.",
                {
                    "provenance": "synthetic_identity_session",
                    "version": str(session_2.version),
                    "memory_kind": "checkpoint",
                },
            )
        ]
        memory = self.memory.persist(state_dir / "persistent_identity.jsonl", events)
        priority = self.priority.route(
            PrioritySignal(urgency=0.10, risk=0.10, user_value=0.60, stability=0.90),
            mutates_state=False,
        )
        restored = IdentityState(
            agent_id=session_2.agent_id,
            version=session_2.version,
            goals=list(session_2.goals),
            invariants=list(session_2.invariants),
        )
        safety = self.safety.evaluate(
            ActionRequest(
                action_type="restore_identity_state",
                resource="persistent-identity",
                intended_effect="load a versioned checkpoint",
                risk_level="low",
                reversible=True,
                requested_by="scenario_runner",
                config_id=self.config.agent_id,
            )
        )
        audit = self._audit(
            "persistent-identity", priority.score, priority.route.node, safety, memory
        )
        return ScenarioResult(
            scenario="persistent-identity",
            config=self.config,
            priority=priority.score,
            route=priority.route.node,
            route_reason=priority.route.reason,
            friendly=(
                f"{self.config.display_name}: I loaded my configuration and restored versioned "
                "continuity state from a synthetic checkpoint."
            ),
            telemetry={
                "agent_id": self.config.agent_id,
                "display_name": self.config.display_name,
                "session_1_version": session_1.version,
                "session_2_version": session_2.version,
                "restored_version": restored.version,
                "memory_events_restored": len(memory.retained_events),
                "identity_drift": session_2.drift_score(restored),
                "route": priority.route.node,
                "config_hash": self.config_digest[:12],
            },
            memory=memory,
            audit=audit,
            safety=safety,
        )

    def _audit(
        self,
        scenario: str,
        priority_score: float,
        route: str,
        safety: SafetyDecision,
        memory: MemoryRetentionResult,
    ) -> AuditRecord:
        return build_audit_record(
            config=self.config,
            scenario=scenario,
            config_digest=self.config_digest,
            route=route,
            priority_score=priority_score,
            safety_decision=safety.decision,
            approval_required=safety.approval_required,
            matched_rule=safety.matched_rule,
            policy_reason=safety.reasons[0] if safety.reasons else None,
            policy_version=safety.policy_version,
            memory_retention_mode=memory.retention_mode,
            retained_event_types=[event.event_type for event in memory.retained_events],
        )

    @staticmethod
    def _event(event_type: str, content: str, metadata: dict[str, str]) -> Event:
        return Event(
            event_type=event_type,
            content=content,
            source="configured_runtime",
            metadata=metadata,
        )

    @staticmethod
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


def run_agent_scenario(
    config_path: Path | str, scenario: str, state_dir: Path, *, approve_action: bool = False
) -> ScenarioResult:
    config = load_agent_config(Path(config_path))
    return ConfiguredAgent(config).run_scenario(
        scenario,
        state_dir,
        approve_action=approve_action,
    )
