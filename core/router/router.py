from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteDecision:
    node: str
    reason: str
    requires_approval: bool = False


class Router:
    def route(self, *, priority: float, mutates_state: bool) -> RouteDecision:
        if mutates_state:
            return RouteDecision("orchestration_node", "mutating action requires policy gate", True)
        if priority >= 0.75:
            return RouteDecision("reflex_node", "high priority signal")
        return RouteDecision("deliberation_node", "normal planning path")

