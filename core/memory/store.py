"""Append-only JSONL event store with TF-IDF semantic search and memory pyramid compaction.

Extends the original MemoryStore (append, tail) with search() and compact()
while preserving backward-compatible signatures.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from core.memory.memory_pyramid import MemoryPyramid, TierCapacity, TierDecision
from core.memory.retrieval import (
    ProvenanceRecord,
    compute_provenance_weight,
    compute_salience,
    make_retrieval_scorer,
)
from core.memory.tfidf_index import IndexEntry, TfidfIndex


@dataclass
class Event:
    event_type: str
    content: str
    source: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    """A single result from a memory search."""

    doc_id: str
    score: float
    content: str
    source: str
    event_type: str = ""
    salience: float = 0.0
    provenance_weight: float = 1.0
    provenance_record: ProvenanceRecord | None = None


class MemoryStore:
    """Append-only JSONL event store with semantic search and compaction."""

    def __init__(
        self,
        path: Path,
        *,
        capacity: TierCapacity | None = None,
    ) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._index = TfidfIndex()
        self._pyramid = MemoryPyramid(capacity=capacity or TierCapacity())
        self._scorer = make_retrieval_scorer()
        self._provenance: dict[str, ProvenanceRecord] = {}
        self._rebuild_index()

    # ── Original API (preserved) ────────────────────────────────────────

    def append(self, event: Event) -> None:
        """Append an event to the JSONL store and index it."""
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")
        self._index.add(
            event.event_id,
            f"{event.event_type}: {event.content}",
            source=event.source,
            metadata={"event_type": event.event_type, "timestamp": event.timestamp, **event.metadata},
        )
        self._index.recompute_idf()

    def tail(self, limit: int = 20) -> list[Event]:
        """Return up to `limit` most recent events."""
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        return [Event(**json.loads(line)) for line in lines if line.strip()]

    # ── Semantic search ─────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Search the memory store with a text query.

        Returns top_k SearchResult items ranked by combined TF-IDF
        similarity and salience scoring.
        """
        raw = self._index.search(query, top_k=top_k, scorer=self._scorer)
        results: list[SearchResult] = []
        for entry, score in raw:
            prov = self._provenance.get(entry.doc_id)
            if prov:
                prov.retrieval_count += 1
                prov.sources.append(entry.source)
                prov.last_retrieved = datetime.now(timezone.utc).isoformat()
            else:
                prov = ProvenanceRecord(
                    doc_id=entry.doc_id,
                    retrieval_count=1,
                    sources=[entry.source],
                )
                self._provenance[entry.doc_id] = prov

            salience = compute_salience(entry)
            prov_weight = compute_provenance_weight(prov)
            etype = entry.metadata.get("event_type", "")

            results.append(
                SearchResult(
                    doc_id=entry.doc_id,
                    score=score,
                    content=entry.text,
                    source=entry.source,
                    event_type=etype,
                    salience=salience,
                    provenance_weight=prov_weight,
                    provenance_record=prov,
                )
            )
        return results

    # ── Memory pyramid compaction ───────────────────────────────────────

    def compact(self) -> tuple[list[str], list[str]]:
        """Run pyramid compaction on the index.

        Returns (retained_doc_ids, evicted_doc_ids). Evicted entries
        exceed tier capacity and are candidates for archival/discard.
        """
        retained, evicted_index_entries = self._pyramid.compact(self._index.entries)
        retained_ids = [e.doc_id for e in retained]
        evicted_ids = [e.doc_id for e in evicted_index_entries]
        return retained_ids, evicted_ids

    def tier_counts(self) -> dict[str, int]:
        """Return document counts per memory tier."""
        decisions = self._pyramid.classify_all(self._index.entries)
        return self._pyramid.tier_counts(decisions)

    @property
    def index_size(self) -> int:
        return self._index.size

    # ── Internal ────────────────────────────────────────────────────────

    def _rebuild_index(self) -> None:
        """Reindex all events from the JSONL store (used at init)."""
        self._index.clear()
        if not self.path.exists():
            return
        events = self.tail(limit=5000)  # reindex up to 5K recent events
        for event in events:
            self._index.add(
                event.event_id,
                f"{event.event_type}: {event.content}",
                source=event.source,
                metadata={
                    "event_type": event.event_type,
                    "timestamp": event.timestamp,
                    **event.metadata,
                },
            )
        self._index.recompute_idf()
