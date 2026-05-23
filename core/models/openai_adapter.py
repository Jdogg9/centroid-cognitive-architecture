from __future__ import annotations

import json
import time
from typing import Any

from .base import ModelAdapter
from .errors import ProviderConfigurationError, ProviderResponseError
from .types import ModelRequest, ModelResponse, ModelToolProposal


class OpenAIResponsesAdapter(ModelAdapter):
    capability_path = "responses"

    def generate(self, request: ModelRequest) -> ModelResponse:
        self._require_live_ready()
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise ProviderConfigurationError(
                "install centroid-cognitive-architecture[openai] to use provider 'openai'"
            ) from exc
        started = time.perf_counter()
        client = OpenAI(
            api_key=self._env(self.config.api_key_env), base_url=self._env(self.config.base_url_env)
        )
        payload: dict[str, Any] = {
            "model": self.model_id,
            "input": [m.__dict__ for m in request.messages],
        }
        if request.system:
            payload["instructions"] = request.system
        if request.max_output_tokens is not None:
            payload["max_output_tokens"] = request.max_output_tokens
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        response = client.responses.create(**payload)
        raw = response.model_dump() if hasattr(response, "model_dump") else dict(response)
        return self.normalize_response(raw, request, latency_ms=self._elapsed_ms(started))

    def normalize_response(
        self, raw: dict[str, Any], request: ModelRequest, *, latency_ms: float | None
    ) -> ModelResponse:
        text_parts: list[str] = []
        proposals: list[ModelToolProposal] = []
        for item in raw.get("output", []):
            item_type = item.get("type")
            if item_type == "message":
                for content in item.get("content", []):
                    if content.get("type") in {"output_text", "text"}:
                        text_parts.append(str(content.get("text", "")))
            elif item_type in {"function_call", "tool_call"}:
                name = str(item.get("name", "unknown_tool"))
                arguments = item.get("arguments", {})
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments or "{}")
                    except json.JSONDecodeError as exc:
                        raise ProviderResponseError(
                            "OpenAI tool arguments were not valid JSON"
                        ) from exc
                proposals.append(
                    ModelToolProposal.create(
                        proposal_id=item.get("call_id") or item.get("id"),
                        name=name,
                        arguments=arguments,
                        provider_id=self.provider_id,
                        model_id=self.model_id,
                    )
                )
        text = "\n".join(part for part in text_parts if part).strip()
        audit = self._audit(
            request, latency_ms=latency_ms, tool_count=len(proposals), path="responses"
        )
        return ModelResponse(
            text=text,
            tool_proposals=proposals,
            provider_id=self.provider_id,
            model_id=self.model_id,
            usage=dict(raw.get("usage", {})),
            latency_ms=latency_ms,
            finish_reason=raw.get("status"),
            capabilities=self.capabilities(),
            provider_metadata={"response_id": raw.get("id")},
            audit=audit,
        )
