from __future__ import annotations

from dataclasses import dataclass

from core.agent_config import PriorityPolicy
from core.priority import PrioritySignal
from core.router import RouteDecision


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class ConfiguredPriorityResult:
    score: float
    route: RouteDecision


class ConfiguredPriorityScorer:
    def __init__(self, policy: PriorityPolicy):
        self.policy = policy

    def score(self, signal: PrioritySignal) -> float:
        total = (
            self.policy.weights.urgency
            + self.policy.weights.risk
            + self.policy.weights.user_value
            + self.policy.weights.instability
        )
        if total <= 0:
            return 0.0
        score = (
            self.policy.weights.urgency * _clamp(signal.urgency)
            + self.policy.weights.risk * _clamp(signal.risk)
            + self.policy.weights.user_value * _clamp(signal.user_value)
            + self.policy.weights.instability * (1.0 - _clamp(signal.stability))
        ) / total
        return round(_clamp(score), 4)

    def route(self, signal: PrioritySignal, *, mutates_state: bool) -> ConfiguredPriorityResult:
        score = self.score(signal)
        if mutates_state:
            return ConfiguredPriorityResult(
                score=score,
                route=RouteDecision(
                    "orchestration_node",
                    "configured runtime routed mutating work through orchestration",
                    True,
                ),
            )
        if score >= self.policy.reflex_threshold:
            return ConfiguredPriorityResult(
                score=score,
                route=RouteDecision("reflex_node", "configured reflex threshold met"),
            )
        if score >= self.policy.deliberation_threshold:
            return ConfiguredPriorityResult(
                score=score,
                route=RouteDecision("deliberation_node", "configured deliberation threshold met"),
            )
        return ConfiguredPriorityResult(
            score=score,
            route=RouteDecision(
                "deliberation_node", "configured low-priority deliberation fallback"
            ),
        )
