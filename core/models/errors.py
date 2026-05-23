from __future__ import annotations


class ProviderError(RuntimeError):
    """Base class for sanitized provider-layer failures."""


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is missing, invalid, or unsafe to use."""


class ProviderResponseError(ProviderError):
    """Raised when provider responses cannot be normalized."""
