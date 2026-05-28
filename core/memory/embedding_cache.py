"""Optional embedding cache for semantic search acceleration.

If OLLAMA_HOST or CENTROID_OLLAMA_URL is set, provides a sha256-keyed
in-process cache that wraps embedding calls. On cache hit, returns
cached vector in < 1ms instead of re-calling the embedding service.

Without any embedding env var set, this module is inert — Centroid
operates on TF-IDF alone.
"""

from __future__ import annotations

import hashlib
import os
import time
from typing import Callable

# ── Configuration ─────────────────────────────────────────────────────────

OLLAMA_HOST: str | None = os.environ.get("OLLAMA_HOST") or os.environ.get("CENTROID_OLLAMA_URL")
EMBED_MODEL: str = os.environ.get("CENTROID_EMBED_MODEL", "nomic-embed-text:latest")

_embedding_provider: Callable[[str], list[float]] | None = None

# ── In-process cache ──────────────────────────────────────────────────────

_EMBED_CACHE: dict[str, list[float]] = {}
_cache_hits: int = 0
_cache_misses: int = 0


def _cache_key(text: str) -> str:
    """Deterministic cache key for a text string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cached_embed(text: str) -> tuple[list[float] | None, float, bool]:
    """Return (vector, latency_ms, was_cache_hit).

    Returns (None, 0.0, False) if no embedding provider is configured.
    """
    global _cache_hits, _cache_misses

    if _embedding_provider is None:
        return None, 0.0, False

    key = _cache_key(text)
    if key in _EMBED_CACHE:
        _cache_hits += 1
        return _EMBED_CACHE[key], 0.0, True

    t0 = time.perf_counter()
    try:
        vector = _embedding_provider(text)
    except Exception:
        return None, (time.perf_counter() - t0) * 1000, False

    latency_ms = (time.perf_counter() - t0) * 1000.0
    _EMBED_CACHE[key] = vector
    _cache_misses += 1
    return vector, latency_ms, False


def set_embedding_provider(provider: Callable[[str], list[float]]) -> None:
    """Register a custom embedding function.

    Typically wraps an Ollama /embed API call if available.
    """
    global _embedding_provider
    _embedding_provider = provider


def cache_stats() -> dict[str, int]:
    """Return hit/miss counts for telemetry."""
    return {
        "hits": _cache_hits,
        "misses": _cache_misses,
        "cache_size": len(_EMBED_CACHE),
    }


def clear_cache() -> None:
    """Reset the embedding cache (useful for testing)."""
    global _cache_hits, _cache_misses
    _EMBED_CACHE.clear()
    _cache_hits = 0
    _cache_misses = 0
