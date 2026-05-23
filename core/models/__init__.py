from __future__ import annotations

from .anthropic_adapter import AnthropicMessagesAdapter
from .base import ModelAdapter
from .mock_adapter import MockModelAdapter
from .openai_adapter import OpenAIResponsesAdapter
from .openai_compatible_adapter import OpenAICompatibleAdapter
from .registry import available_provider_ids, get_provider_config, load_provider_config


def create_provider_adapter(
    provider_id: str, *, live: bool = False, model: str | None = None
) -> ModelAdapter:
    config = get_provider_config(provider_id)
    adapter_type = config.adapter_type
    if adapter_type == "mock":
        return MockModelAdapter(config, live=live, model_override=model)
    if adapter_type == "openai":
        return OpenAIResponsesAdapter(config, live=live, model_override=model)
    if adapter_type == "anthropic":
        return AnthropicMessagesAdapter(config, live=live, model_override=model)
    if adapter_type == "openai_compatible":
        return OpenAICompatibleAdapter(config, live=live, model_override=model)
    from .errors import ProviderConfigurationError

    raise ProviderConfigurationError(f"unsupported provider adapter_type: {adapter_type}")


__all__ = [
    "AnthropicMessagesAdapter",
    "ModelAdapter",
    "MockModelAdapter",
    "OpenAICompatibleAdapter",
    "OpenAIResponsesAdapter",
    "available_provider_ids",
    "create_provider_adapter",
    "get_provider_config",
    "load_provider_config",
]
