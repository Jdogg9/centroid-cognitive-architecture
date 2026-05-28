"""Sensory encoder — normalize arbitrary observation dicts into flat,
key-sorted PerceivedText with truncation.
"""

from __future__ import annotations

import time
from typing import Any

from nodes.sensory_node import PerceivedText

MAX_CONTENT_CHARS = 512


class SensoryEncoder:
    """Flatten and normalize observation dicts into PerceivedText."""

    def encode(
        self, observation: dict, source_id: str = "observation"
    ) -> PerceivedText:
        """Flatten nested dict to dot-joined key=value pairs.

        Only leaf values that are int, float, str, or bool are included.
        Truncates to MAX_CONTENT_CHARS with a "...[truncated]" suffix.
        """
        flat = self._flatten(observation)
        parts = [f"{k}={v}" for k, v in sorted(flat.items())]
        content = ", ".join(parts)

        if len(content) > MAX_CONTENT_CHARS:
            content = content[: MAX_CONTENT_CHARS - len("...[truncated]")] + "...[truncated]"

        return PerceivedText(
            source_kind="sensory",
            content=content,
            source_id=source_id,
            timestamp=time.time(),
        )

    def encode_batch(
        self,
        observations: list[dict],
        source_prefix: str = "obs",
    ) -> list[PerceivedText]:
        """Encode a batch of observations, one PerceivedText each."""
        results: list[PerceivedText] = []
        for i, obs in enumerate(observations):
            sid = f"{source_prefix}_{i}"
            results.append(self.encode(obs, source_id=sid))
        return results

    @staticmethod
    def _flatten(d: dict, parent_key: str = "") -> dict[str, str]:
        """Recursively flatten a nested dict to dot-joined keys.

        Only leaf values that are int, float, str, or bool are included.
        """
        items: dict[str, str] = {}
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else str(k)
            if isinstance(v, dict):
                items.update(SensoryEncoder._flatten(v, new_key))
            elif isinstance(v, (int, float, str, bool)):
                items[new_key] = str(v)
        return items
