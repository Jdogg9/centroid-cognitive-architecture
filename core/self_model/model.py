from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SelfModelSnapshot:
    """Runtime self-model: health and state, not subjective awareness."""

    nodes_alive: int
    nodes_total: int
    active_goals: list[str] = field(default_factory=list)
    known_failures: list[str] = field(default_factory=list)

    @property
    def health_ratio(self) -> float:
        if self.nodes_total <= 0:
            return 0.0
        return self.nodes_alive / self.nodes_total

    @property
    def status(self) -> str:
        if self.health_ratio == 1.0:
            return "healthy"
        if self.health_ratio > 0.0:
            return "degraded"
        return "critical"
