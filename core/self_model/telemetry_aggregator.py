"""Synchronous telemetry aggregator — collects metrics from registered sources.

No threads, no async. Sources are pull-based: each `read()` call returns
the current metric snapshot dict. Fault-tolerant: a failing source
never crashes the aggregator.
"""

from __future__ import annotations

from typing import Protocol


class TelemetrySource(Protocol):
    """Duck-typed protocol: anything with source_id and read()."""

    @property
    def source_id(self) -> str: ...

    def read(self) -> dict[str, float]: ...


class TelemetryAggregator:
    """Synchronous pull-model telemetry fan-in."""

    def __init__(self) -> None:
        self._sources: dict[str, TelemetrySource] = {}

    @property
    def source_ids(self) -> list[str]:
        """Return registered source IDs."""
        return list(self._sources.keys())

    def register(self, source: TelemetrySource) -> None:
        """Register a telemetry source. Re-registering an existing source_id
        overwrites the previous registration."""
        self._sources[source.source_id] = source

    def unregister(self, source_id: str) -> None:
        """Remove a registered source (no-op if not found)."""
        self._sources.pop(source_id, None)

    def collect(self) -> dict[str, dict[str, float]]:
        """Pull metrics from all registered sources.

        Returns {source_id: {metric_key: value}}. Fault-tolerant:
        sources that raise get replaced with {"error": 1.0}.
        """
        result: dict[str, dict[str, float]] = {}
        for source_id, source in self._sources.items():
            try:
                metrics = source.read()
                if not isinstance(metrics, dict):
                    metrics = {"error": 1.0}
                result[source_id] = dict(metrics)
            except Exception:
                result[source_id] = {"error": 1.0}
        return result
