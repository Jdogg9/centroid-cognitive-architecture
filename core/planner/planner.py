from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlanStep:
    description: str
    mutates_state: bool = False
    requires_approval: bool = False


@dataclass
class Plan:
    objective: str
    steps: list[PlanStep] = field(default_factory=list)

    def requires_approval(self) -> bool:
        return any(step.mutates_state or step.requires_approval for step in self.steps)

