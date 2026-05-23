from __future__ import annotations

import json
import time
from typing import Any
from urllib import request as urlrequest

from .base import ModelAdapter
from .errors import ProviderConfigurationError, ProviderResponseError
from .types import ModelRequest, ModelResponse, ModelToolProposal


class OpenAICompatibleAdapter(ModelAdapter):
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.capability_path = self.config.protocol

    def generate(self, request: ModelRequest) -> ModelResponse:
        self._require_live_ready()
        base_url = self._env(self.config.base_url_env) or self.config.default_base_url
        if not base_url:
            raise ProviderConfigurationError(
                f"provider '{self.provider_id}' requires "
                f"{self.config.base_url_env or 'a base URL'} for --live"
            )
        started = time.perf_counter()
        if self.config.protocol == "responses":
            endpoint = base_url.rstrip("/") + "/responses"
            payload = {"model": self.model_id, "input": [m.__dict__ for m in request.messages]}
            raw = self._post_json(endpoint, payload)
            return self.normalize_response(raw, request, latency_ms=self._elapsed_ms(started))
        endpoint = base_url.rstrip("/") + "/chat/completions"
        payload = {"model": self.model_id, "messages": [m.__dict__ for m in request.messages]}
        raw = self._post_json(endpoint, payload)
        return self.normalize_chat_completions(raw, request, latency_ms=self._elapsed_ms(started))

    def _post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        api_key = self._env(self.config.api_key_env) if self.config.api_key_env else None
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        req = urlrequest.Request(endpoint, data=body, headers=headers, method="POST")
        with urlrequest.urlopen(
            req, timeout=30
        ) as response:  # noqa: S310 - opt-in live endpoint from config
            return json.loads(response.read().decode("utf-8"))

    def normalize_response(
        self, raw: dict[str, Any], request: ModelRequest, *, latency_ms: float | None
    ) -> ModelResponse:
        from .openai_adapter import OpenAIResponsesAdapter

        helper = OpenAIResponsesAdapter(self.config, live=self.live, model_override=self.model_id)
        return helper.normalize_response(raw, request, latency_ms=latency_ms)

    def normalize_chat_completions(
        self, raw: dict[str, Any], request: ModelRequest, *, latency_ms: float | None
    ) -> ModelResponse:
        choices = raw.get("choices", [])
        text_parts: list[str] = []
        proposals: list[ModelToolProposal] = []
        finish_reason = None
        for choice in choices:
            finish_reason = choice.get("finish_reason", finish_reason)
            message = choice.get("message", {})
            if message.get("content"):
                text_parts.append(str(message["content"]))
            for tool_call in message.get("tool_calls", []) or []:
                function = tool_call.get("function", {})
                arguments = function.get("arguments", {})
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments or "{}")
                    except json.JSONDecodeError as exc:
                        raise ProviderResponseError(
                            "OpenAI-compatible tool arguments were not valid JSON"
                        ) from exc
                proposals.append(
                    ModelToolProposal.create(
                        proposal_id=tool_call.get("id"),
                        name=str(function.get("name", "unknown_tool")),
                        arguments=arguments,
                        provider_id=self.provider_id,
                        model_id=self.model_id,
                    )
                )
        audit = self._audit(
            request, latency_ms=latency_ms, tool_count=len(proposals), path="chat_completions"
        )
        return ModelResponse(
            text="\n".join(part for part in text_parts if part).strip(),
            tool_proposals=proposals,
            provider_id=self.provider_id,
            model_id=self.model_id,
            usage=dict(raw.get("usage", {})),
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            capabilities=self.capabilities(),
            provider_metadata={"response_id": raw.get("id")},
            audit=audit,
        )
