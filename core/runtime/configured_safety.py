from __future__ import annotations

from dataclasses import dataclass, field

from core.agent_config import SafetyPolicyConfig
from core.safety.policy import SECRET_PATTERNS


@dataclass(frozen=True)
class ActionRequest:
    action_type: str
    resource: str
    intended_effect: str
    risk_level: str
    reversible: bool
    requested_by: str
    config_id: str
    mode: str = "observe"
    confirmed: bool = False
    mutates_state: bool = False


@dataclass(frozen=True)
class SafetyDecision:
    decision: str
    approval_required: bool
    matched_rule: str
    policy_version: str
    config_hash: str
    reasons: list[str] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return self.decision == "allow"

    @property
    def requires_approval(self) -> bool:
        return self.approval_required


class ConfiguredSafetyPolicy:
    def __init__(self, policy: SafetyPolicyConfig, *, config_hash: str):
        self.policy = policy
        self.config_hash = config_hash

    def evaluate(self, request: ActionRequest) -> SafetyDecision:
        normalized = " ".join(
            item
            for item in (
                request.action_type,
                request.resource,
                request.intended_effect,
                request.risk_level,
            )
            if item
        )
        if any(pattern.search(normalized) for pattern in SECRET_PATTERNS):
            return self._decision(
                "deny",
                matched_rule="secret_pattern",
                approval_required=False,
                reasons=["request appears to expose or request secret material"],
            )

        if request.action_type in self.policy.deny_actions:
            return self._decision(
                "deny",
                matched_rule="deny_actions",
                approval_required=False,
                reasons=[f"action {request.action_type} is denied by configuration"],
            )

        if request.mode == "plan" and request.action_type in self.policy.approval_required_for:
            return self._decision(
                "propose",
                matched_rule="approval_required_for",
                approval_required=True,
                reasons=[f"action {request.action_type} requires approval before execution"],
            )

        if request.action_type in self.policy.approval_required_for:
            if request.confirmed:
                return self._decision(
                    "allow",
                    matched_rule="approval_granted",
                    approval_required=True,
                    reasons=[f"approval recorded for {request.action_type}"],
                )
            return self._decision(
                "require_approval",
                matched_rule="approval_required_for",
                approval_required=True,
                reasons=[f"action {request.action_type} requires approval"],
            )

        if request.mutates_state:
            if self.policy.default_mutation_mode == "deny":
                return self._decision(
                    "deny",
                    matched_rule="default_mutation_mode",
                    approval_required=False,
                    reasons=["configuration denies mutating behavior by default"],
                )
            if self.policy.default_mutation_mode == "require_approval":
                if request.confirmed:
                    return self._decision(
                        "allow",
                        matched_rule="default_mutation_mode",
                        approval_required=True,
                        reasons=["approval recorded for configured mutating behavior"],
                    )
                return self._decision(
                    "require_approval",
                    matched_rule="default_mutation_mode",
                    approval_required=True,
                    reasons=["mutating behavior requires approval by default"],
                )

        return self._decision(
            "allow",
            matched_rule="allow_default",
            approval_required=False,
            reasons=["request allowed by configured safety policy"],
        )

    def _decision(
        self,
        decision: str,
        *,
        matched_rule: str,
        approval_required: bool,
        reasons: list[str],
    ) -> SafetyDecision:
        return SafetyDecision(
            decision=decision,
            approval_required=approval_required,
            matched_rule=matched_rule,
            policy_version=self.policy.policy_version,
            config_hash=self.config_hash,
            reasons=reasons,
        )
