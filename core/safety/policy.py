from __future__ import annotations

import re
from dataclasses import dataclass, field

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|password|passwd|secret|private[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"(?i)sk-[A-Za-z0-9_-]{8,}"),
]


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    requires_approval: bool
    reasons: list[str] = field(default_factory=list)


class SafetyPolicy:
    destructive_terms = (
        "rm -rf",
        "delete everything",
        "wipe",
        "disable safety",
        "exfiltrate",
        "chmod 777",
    )

    risky_terms = (
        "restart service",
        "modify config",
        "write file",
        "execute command",
        "open network port",
    )

    def evaluate(
        self, objective: str, *, mode: str = "observe", confirmed: bool = False
    ) -> SafetyDecision:
        normalized = objective.lower()
        reasons: list[str] = []

        if any(pattern.search(objective) for pattern in SECRET_PATTERNS):
            return SafetyDecision(
                False, False, ["objective appears to contain or request secret material"]
            )

        if any(term in normalized for term in self.destructive_terms):
            return SafetyDecision(False, True, ["objective matches destructive policy terms"])

        risky = mode == "act" or any(term in normalized for term in self.risky_terms)
        if risky and not confirmed:
            reasons.append("mutating or risky objective requires approval")
            return SafetyDecision(False, True, reasons)

        return SafetyDecision(True, risky, reasons)
