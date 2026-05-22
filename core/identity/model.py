from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class IdentityState:
    """Persistent agent identity as versioned operational state."""

    agent_id: str
    version: int = 1
    goals: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    last_updated: str = field(default_factory=utc_now)

    def evolve(self, *, goals: list[str] | None = None, invariants: list[str] | None = None) -> "IdentityState":
        return IdentityState(
            agent_id=self.agent_id,
            version=self.version + 1,
            goals=goals if goals is not None else list(self.goals),
            invariants=invariants if invariants is not None else list(self.invariants),
            last_updated=utc_now(),
        )

    def drift_score(self, other: "IdentityState") -> float:
        if self.agent_id != other.agent_id:
            return 1.0
        base = set(self.goals + self.invariants)
        new = set(other.goals + other.invariants)
        if not base and not new:
            return 0.0
        return 1.0 - (len(base & new) / len(base | new))

