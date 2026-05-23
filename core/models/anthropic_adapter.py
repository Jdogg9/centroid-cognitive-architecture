from __future__ import annotations

import time
from typing import Any

from .base import ModelAdapter
from .errors import ProviderConfigurationError
from .types import ModelRequest, ModelResponse, ModelToolProposal


class AnthropicMessagesAdapter(ModelAdapter):
    capability_path = "messages"

    def generate(self, request: ModelRequest) -> ModelResponse:
        self._require_live_ready()
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:
            raise ProviderConfigurationError(
                "install centroid-cognitive-architecture[anthropic] to use provider 'anthropic'"
            ) from exc
        started = time.perf_counter()
        client = Anthropic(api_key=self._env(self.config.api_key_env))
        response = client.messages.create(
            model=self.model_id,
            max_tokens=request.max_output_tokens or 512,
            system=request.system or None,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
        )
        raw = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return self.normalize_response(raw, request, latency_ms=self._elapsed_ms(started))

    def normalize_response(
        self, raw: dict[str, Any], request: ModelRequest, *, latency_ms: float | None
    ) -> ModelResponse:
        text_parts: list[str] = []
        proposals: list[ModelToolProposal] = []
        for block in raw.get("content", []):
            block_type = block.get("type")
            if block_type == "text":
                text_parts.append(str(block.get("text", "")))
            elif block_type == "tool_use":
                proposals.append(
                    ModelToolProposal.create(
                        proposal_id=block.get("id"),
                        name=str(block.get("name", "unknown_tool")),
                        arguments=dict(block.get("input", {})),
                        provider_id=self.provider_id,
                        model_id=self.model_id,
                    )
                )
        audit = self._audit(
            request, latency_ms=latency_ms, tool_count=len(proposals), path="messages"
        )
        return ModelResponse(
            text="\n".join(part for part in text_parts if part).strip(),
            tool_proposals=proposals,
            provider_id=self.provider_id,
            model_id=self.model_id,
            usage=dict(raw.get("usage", {})),
            latency_ms=latency_ms,
            finish_reason=raw.get("stop_reason"),
            capabilities=self.capabilities(),
            provider_metadata={"message_id": raw.get("id")},
            audit=audit,
        )
