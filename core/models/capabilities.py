from __future__ import annotations

from .registry import get_provider_config
from .types import ProviderHealth


def provider_health(provider_id: str, *, live: bool = False) -> ProviderHealth:
    from . import create_provider_adapter

    adapter = create_provider_adapter(provider_id, live=live)
    return adapter.healthcheck(live=live)


def provider_capabilities(provider_id: str):  # type: ignore[no-untyped-def]
    return get_provider_config(provider_id).capabilities
