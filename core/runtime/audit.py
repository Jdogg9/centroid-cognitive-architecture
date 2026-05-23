from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4

from core.agent_config import AgentConfig
from core.models.types import ProviderAuditRecord


@dataclass(frozen=True)
class AuditRecord:
    audit_id: str
    agent_id: str
    display_name: str
    scenario: str
    config_version: str
    config_hash: str | None
    route: str
    priority_score: float
    safety_decision: str
    approval_required: bool
    matched_rule: str | None
    policy_reason: str | None
    policy_version: str
    memory_retention_mode: str
    retained_event_types: list[str]
    provider: ProviderAuditRecord | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def config_hash(config: AgentConfig) -> str:
    payload = json.dumps(config.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_audit_record(
    *,
    config: AgentConfig,
    scenario: str,
    config_digest: str,
    route: str,
    priority_score: float,
    safety_decision: str,
    approval_required: bool,
    matched_rule: str | None,
    policy_reason: str | None,
    policy_version: str,
    memory_retention_mode: str,
    retained_event_types: list[str],
    provider: ProviderAuditRecord | None = None,
) -> AuditRecord:
    return AuditRecord(
        audit_id=str(uuid4()),
        agent_id=config.agent_id,
        display_name=config.display_name,
        scenario=scenario,
        config_version=config.config_version,
        config_hash=config_digest if config.audit_policy.include_config_hash else None,
        route=route,
        priority_score=priority_score,
        safety_decision=safety_decision,
        approval_required=approval_required,
        matched_rule=matched_rule,
        policy_reason=policy_reason if config.audit_policy.include_policy_reason else None,
        policy_version=policy_version,
        memory_retention_mode=memory_retention_mode,
        retained_event_types=list(retained_event_types),
        provider=provider,
    )
