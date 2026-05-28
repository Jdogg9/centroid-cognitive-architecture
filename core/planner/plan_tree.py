"""Plan thread tracking with forecast-linked confidence gates.

PlanTree manages active/completed/abandoned threads. Each thread is
linked to forecasts via forecast_ids. When forecast confidence drops
below the abandon threshold, the thread is auto-abandoned.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from core.planner.planner import PlanStep


@dataclass
class PlanThread:
    """A single execution thread tied to forecast confidence."""

    thread_id: str
    goal: str
    steps: list[PlanStep]
    status: Literal["active", "completed", "abandoned"]
    confidence: float
    created_at: float
    updated_at: float
    forecast_ids: list[str]  # linked Forecast.forecast_id values


class PlanTree:
    """Manage plan threads with confidence-based lifecycle."""

    def __init__(
        self,
        abandon_threshold: float = 0.2,
        state_path: str | Path = "state/plan_tree.json",
    ) -> None:
        self._abandon_threshold = abandon_threshold
        self._path = Path(state_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._threads: dict[str, PlanThread] = {}
        self._load()

    def add_thread(
        self,
        goal: str,
        steps: list[PlanStep],
        initial_confidence: float,
        forecast_ids: list[str] | None = None,
    ) -> PlanThread:
        """Create and register a new active thread."""
        thread = PlanThread(
            thread_id=uuid.uuid4().hex,
            goal=goal,
            steps=list(steps),
            status="active",
            confidence=round(initial_confidence, 6),
            created_at=time.time(),
            updated_at=time.time(),
            forecast_ids=list(forecast_ids or []),
        )
        self._threads[thread.thread_id] = thread
        self._persist()
        return thread

    def update_confidence(self, thread_id: str, new_confidence: float) -> PlanThread:
        """Update a thread's confidence. If below abandon_threshold, set
        status to abandoned."""
        thread = self._threads[thread_id]
        thread.confidence = round(new_confidence, 6)
        thread.updated_at = time.time()
        if new_confidence < self._abandon_threshold:
            thread.status = "abandoned"
        self._persist()
        return thread

    def complete(self, thread_id: str) -> PlanThread:
        """Mark a thread as completed."""
        thread = self._threads[thread_id]
        thread.status = "completed"
        thread.updated_at = time.time()
        self._persist()
        return thread

    def active_threads(self) -> list[PlanThread]:
        """Threads currently active."""
        return [t for t in self._threads.values() if t.status == "active"]

    def all_threads(self) -> list[PlanThread]:
        """All threads regardless of status."""
        return list(self._threads.values())

    def get(self, thread_id: str) -> PlanThread | None:
        """Get a thread by ID, or None."""
        return self._threads.get(thread_id)

    # ── Persistence ───────────────────────────────────────────────────────

    def _persist(self) -> None:
        """Atomic write to state/plan_tree.json."""
        data = {
            "abandon_threshold": self._abandon_threshold,
            "threads": [_serialize_thread(t) for t in self._threads.values()],
        }
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self._path)

    def _load(self) -> None:
        """Load threads from disk. No-op if file missing."""
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._abandon_threshold = float(data.get("abandon_threshold", self._abandon_threshold))
            for raw in data.get("threads", []):
                thread = _deserialize_thread(raw)
                self._threads[thread.thread_id] = thread
        except (json.JSONDecodeError, KeyError, TypeError):
            pass


# ── Serialization helpers ─────────────────────────────────────────────────


def _serialize_thread(t: PlanThread) -> dict:
    return {
        "thread_id": t.thread_id,
        "goal": t.goal,
        "steps": [
            {
                "description": s.description,
                "mutates_state": s.mutates_state,
                "requires_approval": s.requires_approval,
            }
            for s in t.steps
        ],
        "status": t.status,
        "confidence": t.confidence,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
        "forecast_ids": list(t.forecast_ids),
    }


def _deserialize_thread(raw: dict) -> PlanThread:
    return PlanThread(
        thread_id=raw["thread_id"],
        goal=raw["goal"],
        steps=[PlanStep(**s) for s in raw.get("steps", [])],
        status=raw["status"],
        confidence=float(raw["confidence"]),
        created_at=float(raw["created_at"]),
        updated_at=float(raw["updated_at"]),
        forecast_ids=list(raw.get("forecast_ids", [])),
    )
