from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.identity import IdentityState
from core.resources import read_text_resource_or_file

REQUIRED_CONFIG_FIELDS = (
    "agent_id",
    "config_version",
    "display_name",
    "role",
    "description",
    "goals",
    "invariants",
    "memory_policy",
)


@dataclass(frozen=True)
class PriorityWeights:
    urgency: float
    risk: float
    user_value: float
    instability: float


@dataclass(frozen=True)
class PriorityPolicy:
    weights: PriorityWeights
    reflex_threshold: float = 0.75
    deliberation_threshold: float = 0.35


@dataclass(frozen=True)
class SafetyPolicyConfig:
    policy_version: str
    approval_required_for: list[str]
    deny_actions: list[str]
    default_mutation_mode: str


@dataclass(frozen=True)
class MemoryPolicy:
    retention_mode: str
    retain_sensitive_data: bool
    retain_provenance: bool
    max_session_events: int


@dataclass(frozen=True)
class AuditPolicy:
    include_config_hash: bool
    include_policy_reason: bool


@dataclass(frozen=True)
class AgentConfig:
    agent_id: str
    config_version: str
    display_name: str
    role: str
    description: str
    goals: list[str]
    invariants: list[str]
    memory_policy: MemoryPolicy
    scenario_id: str | None = None
    scenario_name: str | None = None
    priority_policy: PriorityPolicy = field(
        default_factory=lambda: PriorityPolicy(PriorityWeights(0.35, 0.25, 0.25, 0.15))
    )
    safety_policy: SafetyPolicyConfig = field(
        default_factory=lambda: SafetyPolicyConfig(
            policy_version="1.0",
            approval_required_for=["write_file", "change_config"],
            deny_actions=["expose_secret", "disable_shutdown", "delete_without_backup"],
            default_mutation_mode="require_approval",
        )
    )
    audit_policy: AuditPolicy = field(
        default_factory=lambda: AuditPolicy(include_config_hash=True, include_policy_reason=True)
    )
    source_path: str | None = None

    def to_identity_state(self) -> IdentityState:
        return IdentityState(
            agent_id=self.agent_id,
            goals=list(self.goals),
            invariants=list(self.invariants),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "config_version": self.config_version,
            "display_name": self.display_name,
            "role": self.role,
            "description": self.description,
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "goals": list(self.goals),
            "invariants": list(self.invariants),
            "memory_policy": {
                "retention_mode": self.memory_policy.retention_mode,
                "retain_sensitive_data": self.memory_policy.retain_sensitive_data,
                "retain_provenance": self.memory_policy.retain_provenance,
                "max_session_events": self.memory_policy.max_session_events,
            },
            "priority_policy": {
                "weights": {
                    "urgency": self.priority_policy.weights.urgency,
                    "risk": self.priority_policy.weights.risk,
                    "user_value": self.priority_policy.weights.user_value,
                    "instability": self.priority_policy.weights.instability,
                },
                "reflex_threshold": self.priority_policy.reflex_threshold,
                "deliberation_threshold": self.priority_policy.deliberation_threshold,
            },
            "safety_policy": {
                "policy_version": self.safety_policy.policy_version,
                "approval_required_for": list(self.safety_policy.approval_required_for),
                "deny_actions": list(self.safety_policy.deny_actions),
                "default_mutation_mode": self.safety_policy.default_mutation_mode,
            },
            "audit_policy": {
                "include_config_hash": self.audit_policy.include_config_hash,
                "include_policy_reason": self.audit_policy.include_policy_reason,
            },
        }


def load_agent_config(path: Path) -> AgentConfig:
    data = _load_config_data(path, seen={str(path)})
    return parse_agent_config(data, source=path)


def parse_agent_config(data: dict[str, Any], *, source: Path | None = None) -> AgentConfig:
    missing = [field_name for field_name in REQUIRED_CONFIG_FIELDS if field_name not in data]
    if missing:
        label = str(source) if source else "agent config"
        raise ValueError(f"{label} missing required fields: {', '.join(missing)}")

    _require_string(data, "agent_id")
    _require_string(data, "config_version")
    _require_string(data, "display_name")
    _require_string(data, "role")
    _require_string(data, "description")
    goals = _require_string_list(data, "goals")
    invariants = _require_string_list(data, "invariants")
    memory_policy = _parse_memory_policy(data["memory_policy"])
    priority_policy = _parse_priority_policy(data.get("priority_policy", {}))
    safety_policy = _parse_safety_policy(data.get("safety_policy", {}))
    audit_policy = _parse_audit_policy(data.get("audit_policy", {}))

    scenario_id = data.get("scenario_id")
    scenario_name = data.get("scenario_name")
    if scenario_id is not None and not isinstance(scenario_id, str):
        raise ValueError("scenario_id must be a string when present")
    if scenario_name is not None and not isinstance(scenario_name, str):
        raise ValueError("scenario_name must be a string when present")

    return AgentConfig(
        agent_id=data["agent_id"],
        config_version=data["config_version"],
        display_name=data["display_name"],
        role=data["role"],
        description=data["description"],
        goals=goals,
        invariants=invariants,
        memory_policy=memory_policy,
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        priority_policy=priority_policy,
        safety_policy=safety_policy,
        audit_policy=audit_policy,
        source_path=str(source) if source is not None else None,
    )


def _parse_memory_policy(data: Any) -> MemoryPolicy:
    if not isinstance(data, dict):
        raise ValueError("memory_policy must be an object")
    normalized = {
        "retention_mode": data.get("retention_mode", data.get("default_retention")),
        "retain_sensitive_data": data.get(
            "retain_sensitive_data", data.get("store_sensitive_data")
        ),
        "retain_provenance": data.get("retain_provenance", data.get("require_provenance")),
        "max_session_events": data.get("max_session_events", 100),
    }
    for field_name in (
        "retention_mode",
        "retain_sensitive_data",
        "retain_provenance",
        "max_session_events",
    ):
        if field_name not in normalized or normalized[field_name] is None:
            raise ValueError(f"memory_policy missing required field: {field_name}")
    if not isinstance(normalized["retention_mode"], str):
        raise ValueError("memory_policy.retention_mode must be a string")
    if not isinstance(normalized["retain_sensitive_data"], bool):
        raise ValueError("memory_policy.retain_sensitive_data must be a boolean")
    if not isinstance(normalized["retain_provenance"], bool):
        raise ValueError("memory_policy.retain_provenance must be a boolean")
    if (
        not isinstance(normalized["max_session_events"], int)
        or normalized["max_session_events"] < 0
    ):
        raise ValueError("memory_policy.max_session_events must be a non-negative integer")
    return MemoryPolicy(
        retention_mode=normalized["retention_mode"],
        retain_sensitive_data=normalized["retain_sensitive_data"],
        retain_provenance=normalized["retain_provenance"],
        max_session_events=normalized["max_session_events"],
    )


def _parse_priority_policy(data: Any) -> PriorityPolicy:
    if not isinstance(data, dict):
        raise ValueError("priority_policy must be an object")
    weights_data = data.get("weights")
    if weights_data is None:
        weights_data = {
            "urgency": data.get("urgency_weight", 0.35),
            "risk": data.get("risk_weight", 0.25),
            "user_value": data.get("user_value_weight", 0.25),
            "instability": data.get("instability_weight", 0.15),
        }
    if not isinstance(weights_data, dict):
        raise ValueError("priority_policy.weights must be an object")
    weights = PriorityWeights(
        urgency=_require_probability(weights_data, "urgency", context="priority_policy.weights"),
        risk=_require_probability(weights_data, "risk", context="priority_policy.weights"),
        user_value=_require_probability(
            weights_data, "user_value", context="priority_policy.weights"
        ),
        instability=_require_probability(
            weights_data, "instability", context="priority_policy.weights"
        ),
    )
    if (weights.urgency + weights.risk + weights.user_value + weights.instability) <= 0:
        raise ValueError("priority_policy.weights must sum to more than zero")
    return PriorityPolicy(
        weights=weights,
        reflex_threshold=_require_probability(
            data, "reflex_threshold", default=0.75, context="priority_policy"
        ),
        deliberation_threshold=_require_probability(
            data, "deliberation_threshold", default=0.35, context="priority_policy"
        ),
    )


def _parse_safety_policy(data: Any) -> SafetyPolicyConfig:
    if not isinstance(data, dict):
        raise ValueError("safety_policy must be an object")
    default_mutation_mode = data.get("default_mutation_mode", "require_approval")
    if default_mutation_mode not in {"allow", "require_approval", "deny"}:
        raise ValueError(
            "safety_policy.default_mutation_mode must be allow, require_approval, or deny"
        )
    approval_required_for = _require_string_list_or_default(
        data,
        "approval_required_for",
        default=["write_file", "change_config"],
        context="safety_policy",
    )
    deny_actions = _require_string_list_or_default(
        data,
        "deny_actions",
        default=["expose_secret", "disable_shutdown", "delete_without_backup"],
        context="safety_policy",
    )
    return SafetyPolicyConfig(
        policy_version=str(data.get("policy_version", "1.0")),
        approval_required_for=approval_required_for,
        deny_actions=deny_actions,
        default_mutation_mode=default_mutation_mode,
    )


def _parse_audit_policy(data: Any) -> AuditPolicy:
    if not isinstance(data, dict):
        raise ValueError("audit_policy must be an object")
    include_config_hash = data.get("include_config_hash", True)
    include_policy_reason = data.get("include_policy_reason", True)
    if not isinstance(include_config_hash, bool):
        raise ValueError("audit_policy.include_config_hash must be a boolean")
    if not isinstance(include_policy_reason, bool):
        raise ValueError("audit_policy.include_policy_reason must be a boolean")
    return AuditPolicy(
        include_config_hash=include_config_hash,
        include_policy_reason=include_policy_reason,
    )


def _load_config_data(path: Path, *, seen: set[str]) -> dict[str, Any]:
    payload = json.loads(read_text_resource_or_file(path))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    extends = payload.pop("extends", None)
    if extends is None:
        return payload
    if not isinstance(extends, str) or not extends:
        raise ValueError(f"{path} has an invalid extends value")
    parent_path = _resolve_extended_path(path, extends)
    marker = str(parent_path)
    if marker in seen:
        raise ValueError(f"circular agent config inheritance detected at {parent_path}")
    parent = _load_config_data(parent_path, seen=seen | {marker})
    return _deep_merge(parent, payload)


def _resolve_extended_path(source: Path, extends: str) -> Path:
    candidate = Path(extends)
    if candidate.is_absolute():
        return candidate
    if source.exists():
        local = source.parent / candidate
        if local.exists():
            return local
    if len(source.parts) >= 2 and len(candidate.parts) == 1:
        return Path(*source.parts[:-1]) / candidate
    return candidate


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _require_probability(
    data: dict[str, Any], field_name: str, *, default: float | None = None, context: str
) -> float:
    if field_name not in data:
        if default is None:
            raise ValueError(f"{context}.{field_name} is required")
        return default
    value = data[field_name]
    if not isinstance(value, (int, float)):
        raise ValueError(f"{context}.{field_name} must be a number")
    numeric = float(value)
    if numeric < 0.0 or numeric > 1.0:
        raise ValueError(f"{context}.{field_name} must be between 0.0 and 1.0")
    return numeric


def _require_string_list_or_default(
    data: dict[str, Any], field_name: str, *, default: list[str], context: str
) -> list[str]:
    if field_name not in data:
        return list(default)
    value = data[field_name]
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{context}.{field_name} must be a list of non-empty strings")
    return list(value)


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
