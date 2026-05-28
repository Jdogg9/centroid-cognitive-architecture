"""Memory pyramid: tier classification and compaction logic.

Divides the event store into active → working → long-term → archive
tiers based on recency, salience, and configurable capacity limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from core.memory.retrieval import (
    DEFAULT_EVENT_TYPE_WEIGHTS,
    DEFAULT_SIGNAL_TERMS,
    DEFAULT_SOURCE_WEIGHTS,
    compute_salience,
)
from core.memory.tfidf_index import IndexEntry


# ── Tier definitions ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class TierCapacity:
    """Capacity limits for memory tiers."""

    active: int = 50       # current session context
    working: int = 200     # recent operational state
    long_term: int = 500   # indexed prior facts
    # archive: unlimited — everything else


@dataclass
class TierDecision:
    """Result of tier classification for a single entry."""

    doc_id: str
    tier: str  # "active", "working", "long_term", "archive"
    salience: float
    age_hours: float
    reason: str


# ── Tier classifier ───────────────────────────────────────────────────────


class MemoryPyramid:
    """Assign each indexed entry to a tier and compact when tiers overflow."""

    def __init__(
        self,
        *,
        capacity: TierCapacity | None = None,
        source_weights: dict[str, float] | None = None,
        event_type_weights: dict[str, float] | None = None,
        signal_terms: dict[str, float] | None = None,
    ) -> None:
        self.capacity = capacity or TierCapacity()
        self._source_weights = source_weights or DEFAULT_SOURCE_WEIGHTS
        self._event_type_weights = event_type_weights or DEFAULT_EVENT_TYPE_WEIGHTS
        self._signal_terms = signal_terms or DEFAULT_SIGNAL_TERMS

    def classify_one(self, entry: IndexEntry) -> TierDecision:
        """Assign a single entry to a tier based on salience and age."""
        salience = compute_salience(
            entry,
            source_weights=self._source_weights,
            event_type_weights=self._event_type_weights,
            signal_terms=self._signal_terms,
        )
        age_hours = _estimate_age_hours(entry)

        # Tier assignment
        if salience >= 0.5 and age_hours < 1.0:
            tier = "active"
            reason = "high salience, recent"
        elif salience >= 0.3 and age_hours < 24.0:
            tier = "working"
            reason = "medium salience, within 24h"
        elif salience >= 0.2:
            tier = "long_term"
            reason = "moderate salience"
        else:
            tier = "archive"
            reason = "low salience"

        return TierDecision(
            doc_id=entry.doc_id,
            tier=tier,
            salience=salience,
            age_hours=round(age_hours, 1),
            reason=reason,
        )

    def classify_all(self, entries: list[IndexEntry]) -> list[TierDecision]:
        """Classify all entries and return tier assignments."""
        return [self.classify_one(e) for e in entries]

    def compact(
        self,
        entries: list[IndexEntry],
    ) -> tuple[list[IndexEntry], list[IndexEntry]]:
        """Run compaction: return (retained, evicted).

        Active tier gets priority. Within each tier, entries are sorted
        by salience (descending), then by age (ascending — newer first).
        Entries that don't fit the active + working + long_term cap
        are evicted to archive.
        """
        decisions = self.classify_all(entries)
        tier_buckets: dict[str, list[tuple[IndexEntry, TierDecision]]] = {
            "active": [],
            "working": [],
            "long_term": [],
            "archive": [],
        }

        for entry, decision in zip(entries, decisions):
            tier_buckets[decision.tier].append((entry, decision))

        # Sort each tier: salience desc, then newer first
        for tier in tier_buckets:
            tier_buckets[tier].sort(
                key=lambda x: (-x[1].salience, x[1].age_hours)
            )

        retained: list[IndexEntry] = []
        evicted: list[IndexEntry] = []

        # Fill active
        bucket = tier_buckets["active"]
        retained.extend(e for e, _d in bucket[: self.capacity.active])
        evicted.extend(e for e, _d in bucket[self.capacity.active :])

        # Fill working
        bucket = tier_buckets["working"]
        remaining_working = self.capacity.working - _count_in(retained, decisions, "working")
        if remaining_working > 0:
            working_retained = bucket[:remaining_working]
            retained.extend(e for e, _d in working_retained)
            evicted.extend(e for e, _d in bucket[remaining_working:])
        else:
            evicted.extend(e for e, _d in bucket)

        # Fill long_term
        bucket = tier_buckets["long_term"]
        remaining_lt = self.capacity.long_term - _count_in(retained, decisions, "long_term")
        if remaining_lt > 0:
            lt_retained = bucket[:remaining_lt]
            retained.extend(e for e, _d in lt_retained)
            evicted.extend(e for e, _d in bucket[remaining_lt:])
        else:
            evicted.extend(e for e, _d in bucket)

        # Archive: always evicted
        evicted.extend(e for e, _d in tier_buckets["archive"])

        return retained, evicted

    def tier_counts(self, decisions: list[TierDecision]) -> dict[str, int]:
        """Return count per tier."""
        counts: dict[str, int] = {"active": 0, "working": 0, "long_term": 0, "archive": 0}
        for d in decisions:
            counts[d.tier] = counts.get(d.tier, 0) + 1
        return counts


# ── Helpers ────────────────────────────────────────────────────────────────


def _estimate_age_hours(entry: IndexEntry) -> float:
    """Estimate entry age in hours from metadata timestamp if present."""
    ts = entry.metadata.get("timestamp", "")
    if not ts:
        return 999.0  # unknown age → very old
    try:
        dt = datetime.fromisoformat(ts)
        # Handle timezone-naive timestamps
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except (ValueError, TypeError):
        return 999.0


def _count_in(
    retained: list[IndexEntry],
    decisions: list[TierDecision],
    tier: str,
) -> int:
    """Count how many entries from a given tier were retained."""
    d_map = {d.doc_id: d for d in decisions}
    return sum(1 for e in retained if d_map.get(e.doc_id, TierDecision(e.doc_id, "", 0, 0, "")).tier == tier)
