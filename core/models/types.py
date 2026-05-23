from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ModelMessage:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelRequest:
    messages: list[ModelMessage]
    system: str | None = None
    tools: list[ModelToolDefinition] = field(default_factory=list)
    structured_output: dict[str, Any] | None = None
    temperature: float | None = None
    max_output_tokens: int | None = None
    runtime_metadata: dict[str, Any] = field(default_factory=dict)
    scenario_id: str | None = None


@dataclass(frozen=True)
class ModelToolProposal:
    proposal_id: str
    name: str
    arguments: dict[str, Any]
    provider_id: str
    model_id: str
    requires_centroid_policy_evaluation: bool = True
    executed: bool = False

    @classmethod
    def create(
        cls,
        *,
        name: str,
        arguments: dict[str, Any],
        provider_id: str,
        model_id: str,
        proposal_id: str | None = None,
    ) -> ModelToolProposal:
        return cls(
            proposal_id=proposal_id or str(uuid4()),
            name=name,
            arguments=dict(arguments),
            provider_id=provider_id,
            model_id=model_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelCapabilities:
    text_generation: bool = True
    streaming: bool = False
    structured_outputs: bool = False
    tool_proposals: bool = False
    vision: bool = False
    responses_api: bool = False
    chat_completions: bool = False
    provider_managed_conversation_state: bool = False
    remote_mcp: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderHealth:
    provider_id: str
    provider_configured: bool
    adapter_status: str
    capabilities: ModelCapabilities
    reachable: bool | None = None
    sanitized_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["capabilities"] = self.capabilities.to_dict()
        return payload


@dataclass(frozen=True)
class ProviderAuditRecord:
    provider_id: str
    model_id: str
    adapter_type: str
    config_hash: str
    request_id: str
    scenario: str | None
    capability_path_used: str
    latency_ms: float | None
    tool_proposal_count: int
    safety_disposition: str
    secret_redaction_result: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelResponse:
    text: str
    tool_proposals: list[ModelToolProposal]
    provider_id: str
    model_id: str
    usage: dict[str, Any] = field(default_factory=dict)
    latency_ms: float | None = None
    finish_reason: str | None = None
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    audit: ProviderAuditRecord | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["capabilities"] = self.capabilities.to_dict()
        payload["tool_proposals"] = [proposal.to_dict() for proposal in self.tool_proposals]
        payload["audit"] = self.audit.to_dict() if self.audit else None
        return payload


@dataclass(frozen=True)
class ProviderConfig:
    provider_id: str
    adapter_type: str
    model: str
    protocol: str
    capabilities: ModelCapabilities
    api_key_env: str | None = None
    base_url_env: str | None = None
    model_env: str | None = None
    default_base_url: str | None = None
    live_enabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "adapter_type": self.adapter_type,
            "model": self.model,
            "protocol": self.protocol,
            "api_key_env": self.api_key_env,
            "base_url_env": self.base_url_env,
            "model_env": self.model_env,
            "default_base_url": self.default_base_url,
            "live_enabled": self.live_enabled,
            "capabilities": self.capabilities.to_dict(),
            "metadata": dict(self.metadata),
        }
