"""Telemetry encoder — convert health metrics dicts into natural language
PerceivedText for cross-modal comparison.
"""

from __future__ import annotations

import time

from nodes.sensory_node import PerceivedText


class TelemetryEncoder:
    """Convert structured telemetry into PerceivedText."""

    def encode(self, source_id: str, metrics: dict[str, float]) -> PerceivedText:
        """Convert a metrics dict to natural language text.

        Example output:
          "node memory: retrieval_score=0.920 (high), error_rate=0.050"
        """
        parts: list[str] = [f"node {source_id}:"]

        for field in sorted(metrics):
            value = metrics[field]
            part = f"{field}={value:.3f}"
            if value > 0.75:
                part += " (high)"
            elif value < 0.25:
                part += " (low)"
            parts.append(part)

        content = ", ".join(parts)

        return PerceivedText(
            source_kind="telemetry",
            content=content,
            source_id=source_id,
            timestamp=time.time(),
        )

    def encode_snapshot(self, snapshot: dict) -> list[PerceivedText]:
        """Encode a WorldSnapshot-shaped dict's node_health into one
        PerceivedText per node."""
        results: list[PerceivedText] = []
        node_health = snapshot.get("node_health", {})
        if not isinstance(node_health, dict):
            return results

        for node_id, score in node_health.items():
            if isinstance(score, (int, float)):
                metrics: dict[str, float] = {"health_score": float(score)}
                # Also include trend if available
                trends = snapshot.get("node_trends", {})
                if isinstance(trends, dict) and node_id in trends:
                    metrics["trend"] = float(trends[node_id])
                results.append(self.encode(node_id, metrics))

        return results
