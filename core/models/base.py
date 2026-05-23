from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any
from uuid import uuid4

from .errors import ProviderConfigurationError
from .types import (
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ProviderAuditRecord,
    ProviderConfig,
    ProviderHealth,
)

SECRET_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE),
    re.compile(
        r"(api[_-]?key|authorization|token|password|secret)\s*[=:]\s*[^\s,;]+", re.IGNORECASE
    ),
)


def stable_config_hash(config: ProviderConfig) -> str:
    payload = json.dumps(config.public_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ModelAdapter:
    capability_path = "base"

    def __init__(
        self, config: ProviderConfig, *, live: bool = False, model_override: str | None = None
    ):
        self.config = config
        self.live = live
        self.model_id = model_override or self._env(config.model_env) or config.model

    @property
    def provider_id(self) -> str:
        return self.config.provider_id

    @property
    def adapter_type(self) -> str:
        return self.config.adapter_type

    def capabilities(self) -> ModelCapabilities:
        return self.config.capabilities

    def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError("model adapters must implement generate")

    def healthcheck(self, *, live: bool | None = None) -> ProviderHealth:
        live_check = self.live if live is None else live
        if live_check:
            self._require_live_ready()
            return ProviderHealth(
                provider_id=self.provider_id,
                provider_configured=True,
                adapter_status="configured",
                capabilities=self.capabilities(),
                reachable=None,
            )
        return ProviderHealth(
            provider_id=self.provider_id,
            provider_configured=True,
            adapter_status="configured",
            capabilities=self.capabilities(),
            reachable=None,
        )

    def _require_live_ready(self) -> None:
        if not self.live:
            raise ProviderConfigurationError(
                f"provider '{self.provider_id}' requires --live before any network call; "
                "mock mode is the default"
            )
        if self.config.api_key_env and not self._env(self.config.api_key_env):
            raise ProviderConfigurationError(
                f"provider '{self.provider_id}' requires environment variable "
                f"{self.config.api_key_env} for --live"
            )

    def _env(self, name: str | None) -> str | None:
        return os.environ.get(name) if name else None

    def sanitize_error(self, message: str) -> str:
        redacted = message
        for pattern in SECRET_VALUE_PATTERNS:
            redacted = pattern.sub(
                lambda m: f"{m.group(1)}=[redacted]" if m.lastindex else "[redacted]", redacted
            )
        return redacted

    def _audit(
        self,
        request: ModelRequest,
        *,
        latency_ms: float | None,
        tool_count: int,
        path: str | None = None,
        safety_disposition: str = "pending_centroid_policy",
        metadata: dict[str, Any] | None = None,
    ) -> ProviderAuditRecord:
        return ProviderAuditRecord(
            provider_id=self.provider_id,
            model_id=self.model_id,
            adapter_type=self.adapter_type,
            config_hash=stable_config_hash(self.config),
            request_id=str(uuid4()),
            scenario=request.scenario_id,
            capability_path_used=path or self.capability_path,
            latency_ms=latency_ms,
            tool_proposal_count=tool_count,
            safety_disposition=safety_disposition,
            secret_redaction_result="clean",
            metadata=metadata or {},
        )

    def _elapsed_ms(self, started: float) -> float:
        return round((time.perf_counter() - started) * 1000.0, 4)
