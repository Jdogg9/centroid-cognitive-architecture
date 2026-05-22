from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TimingSample:
    loop_name: str
    started_at: datetime
    completed_at: datetime

    @property
    def latency_ms(self) -> float:
        return latency_ms(self.started_at, self.completed_at)


def latency_ms(started_at: datetime, completed_at: datetime) -> float:
    return round((completed_at - started_at).total_seconds() * 1000, 3)
