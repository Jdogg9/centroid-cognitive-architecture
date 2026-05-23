from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.resources import read_text_resource_or_file

from .errors import ProviderConfigurationError
from .types import ModelCapabilities, ProviderConfig

BUILTIN_PROVIDER_PATHS = {
    "mock": "configs/providers/mock.json",
    "openai": "configs/providers/openai.json.example",
    "anthropic": "configs/providers/anthropic.json.example",
    "ollama": "configs/providers/ollama.json.example",
    "vllm": "configs/providers/vllm.json.example",
}


def available_provider_ids() -> list[str]:
    return sorted(BUILTIN_PROVIDER_PATHS)


def get_provider_config(provider_id: str) -> ProviderConfig:
    if provider_id not in BUILTIN_PROVIDER_PATHS:
        raise ProviderConfigurationError(
            f"unknown provider '{provider_id}'. Available providers: "
            f"{', '.join(available_provider_ids())}"
        )
    text = read_text_resource_or_file(BUILTIN_PROVIDER_PATHS[provider_id])
    return load_provider_config(json.loads(text))


def load_provider_config(data_or_path: dict[str, Any] | str | Path) -> ProviderConfig:
    if isinstance(data_or_path, dict):
        data = data_or_path
    else:
        data = json.loads(read_text_resource_or_file(data_or_path))
    for field in ("provider_id", "adapter_type"):
        if field not in data or not isinstance(data[field], str):
            raise ProviderConfigurationError(
                f"provider config missing required string field: {field}"
            )
    capabilities_data = data.get("capabilities", {})
    if not isinstance(capabilities_data, dict):
        raise ProviderConfigurationError("provider config capabilities must be an object")
    capabilities = ModelCapabilities(
        text_generation=bool(capabilities_data.get("text_generation", True)),
        streaming=bool(capabilities_data.get("streaming", False)),
        structured_outputs=bool(capabilities_data.get("structured_outputs", False)),
        tool_proposals=bool(capabilities_data.get("tool_proposals", False)),
        vision=bool(capabilities_data.get("vision", False)),
        responses_api=bool(capabilities_data.get("responses_api", False)),
        chat_completions=bool(capabilities_data.get("chat_completions", False)),
        provider_managed_conversation_state=bool(
            capabilities_data.get("provider_managed_conversation_state", False)
        ),
        remote_mcp=bool(capabilities_data.get("remote_mcp", False)),
        metadata=dict(capabilities_data.get("metadata", {})),
    )
    model = data.get("model", "")
    model_env = data.get("model_env")
    if not model and model_env:
        model = f"${{{model_env}}}"
    return ProviderConfig(
        provider_id=data["provider_id"],
        adapter_type=data["adapter_type"],
        model=str(model or "unspecified-model"),
        protocol=str(data.get("protocol", "mock")),
        api_key_env=data.get("api_key_env"),
        base_url_env=data.get("base_url_env"),
        model_env=model_env,
        default_base_url=data.get("default_base_url"),
        live_enabled=bool(data.get("live_enabled", False)),
        capabilities=capabilities,
        metadata=dict(data.get("metadata", {})),
    )
