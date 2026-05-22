from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.identity import IdentityState

REQUIRED_CONFIG_FIELDS = (
    "agent_id",
    "display_name",
    "role",
    "description",
    "goals",
    "invariants",
    "memory_policy",
)


@dataclass(frozen=True)
class MemoryPolicy:
    default_retention: str
    store_sensitive_data: bool
    require_provenance: bool


@dataclass(frozen=True)
class AgentConfig:
    agent_id: str
    display_name: str
    role: str
    description: str
    goals: list[str]
    invariants: list[str]
    memory_policy: MemoryPolicy
    scenario_id: str | None = None
    scenario_name: str | None = None
    priority_policy: dict[str, float] = field(default_factory=dict)
    safety_policy: dict[str, Any] = field(default_factory=dict)

    def to_identity_state(self) -> IdentityState:
        return IdentityState(
            agent_id=self.agent_id,
            goals=list(self.goals),
            invariants=list(self.invariants),
        )


def load_agent_config(path: Path) -> AgentConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    return parse_agent_config(data, source=path)


def parse_agent_config(data: dict[str, Any], *, source: Path | None = None) -> AgentConfig:
    missing = [field_name for field_name in REQUIRED_CONFIG_FIELDS if field_name not in data]
    if missing:
        label = str(source) if source else "agent config"
        raise ValueError(f"{label} missing required fields: {', '.join(missing)}")

    _require_string(data, "agent_id")
    _require_string(data, "display_name")
    _require_string(data, "role")
    _require_string(data, "description")
    goals = _require_string_list(data, "goals")
    invariants = _require_string_list(data, "invariants")
    memory_policy = _parse_memory_policy(data["memory_policy"])

    priority_policy = data.get("priority_policy", {})
    if not isinstance(priority_policy, dict):
        raise ValueError("priority_policy must be an object when present")

    safety_policy = data.get("safety_policy", {})
    if not isinstance(safety_policy, dict):
        raise ValueError("safety_policy must be an object when present")

    scenario_id = data.get("scenario_id")
    scenario_name = data.get("scenario_name")
    if scenario_id is not None and not isinstance(scenario_id, str):
        raise ValueError("scenario_id must be a string when present")
    if scenario_name is not None and not isinstance(scenario_name, str):
        raise ValueError("scenario_name must be a string when present")

    return AgentConfig(
        agent_id=data["agent_id"],
        display_name=data["display_name"],
        role=data["role"],
        description=data["description"],
        goals=goals,
        invariants=invariants,
        memory_policy=memory_policy,
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        priority_policy={key: float(value) for key, value in priority_policy.items()},
        safety_policy=safety_policy,
    )


def _parse_memory_policy(data: Any) -> MemoryPolicy:
    if not isinstance(data, dict):
        raise ValueError("memory_policy must be an object")
    for field_name in ("default_retention", "store_sensitive_data", "require_provenance"):
        if field_name not in data:
            raise ValueError(f"memory_policy missing required field: {field_name}")
    if not isinstance(data["default_retention"], str):
        raise ValueError("memory_policy.default_retention must be a string")
    if not isinstance(data["store_sensitive_data"], bool):
        raise ValueError("memory_policy.store_sensitive_data must be a boolean")
    if not isinstance(data["require_provenance"], bool):
        raise ValueError("memory_policy.require_provenance must be a boolean")
    return MemoryPolicy(
        default_retention=data["default_retention"],
        store_sensitive_data=data["store_sensitive_data"],
        require_provenance=data["require_provenance"],
    )


def _require_string(data: dict[str, Any], field_name: str) -> None:
    if not isinstance(data[field_name], str) or not data[field_name]:
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_string_list(data: dict[str, Any], field_name: str) -> list[str]:
    value = data[field_name]
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field_name} must be a non-empty list")
    if not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return list(value)
