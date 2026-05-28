"""Public exports for the sensory node package."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class PerceivedText:
    source_kind: Literal["code", "telemetry", "sensory"]
    content: str
    source_id: str
    timestamp: float


from .code_encoder import CodeEncoder
from .latent_projector import LatentProjector, SensoryPipeline
from .sensory_encoder import SensoryEncoder
from .telemetry_encoder import TelemetryEncoder

__all__ = [
    "CodeEncoder",
    "LatentProjector",
    "PerceivedText",
    "SensoryEncoder",
    "SensoryPipeline",
    "TelemetryEncoder",
]
