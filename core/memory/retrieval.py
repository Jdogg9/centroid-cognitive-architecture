"""Salience, provenance, and scoring utilities for memory retrieval.

Extends TF-IDF search with domain-aware scoring so Centroid's memory
system can prioritize high-significance, well-provenanced events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.memory.tfidf_index import IndexEntry, tokenize


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Salience scoring ──────────────────────────────────────────────────────


def compute_salience(
    entry: IndexEntry,
    *,
    source_weights: dict[str, float] | None = None,
    event_type_weights: dict[str, float] | None = None,
    signal_terms: dict[str, float] | None = None,
) -> float:
    """Score how important a document is for retention priority.

    When optional weight dicts are None, DEFAULT_* weights are used.
    """
    score = 0.1
    text_lower = entry.text.lower()

    src_w = source_weights if source_weights is not None else DEFAULT_SOURCE_WEIGHTS
    evt_w = event_type_weights if event_type_weights is not None else DEFAULT_EVENT_TYPE_WEIGHTS
    sig_t = signal_terms if signal_terms is not None else DEFAULT_SIGNAL_TERMS

    # Source-based boost
    score += src_w.get(entry.source, 0.0)

    # Event-type boost from metadata
    etype = entry.metadata.get("event_type", "")
    score += evt_w.get(etype, 0.0)

    # Signal term matching
    for term, weight in sig_t.items():
        if term in text_lower:
            score += weight

    return round(min(score, 1.0), 3)


# Default weights — configurable at runtime
DEFAULT_SOURCE_WEIGHTS: dict[str, float] = {
    "event_journal": 0.18,
    "memory_journal": 0.15,
    "deliberation_log": 0.16,
    "sensory_stream": 0.12,
    "audit_log": 0.20,
}

DEFAULT_EVENT_TYPE_WEIGHTS: dict[str, float] = {
    "decision": 0.22,
    "safety_event": 0.22,
    "session_start": 0.20,
    "session_end": 0.20,
    "checkpoint": 0.18,
    "anomaly": 0.18,
    "correction": 0.16,
}

DEFAULT_SIGNAL_TERMS: dict[str, float] = {
    "error": 0.18,
    "failed": 0.18,
    "anomaly": 0.18,
    "critical": 0.18,
    "warning": 0.14,
    "risk": 0.14,
    "rollback": 0.14,
    "goal": 0.12,
    "plan": 0.12,
    "decision": 0.12,
    "intent": 0.12,
}


# ── Provenance weighting ──────────────────────────────────────────────────


@dataclass
class ProvenanceRecord:
    """Track how many times and from what sources a fact has been retrieved."""

    doc_id: str
    retrieval_count: int = 0
    sources: list[str] = field(default_factory=list)
    last_retrieved: str = field(default_factory=utc_now_iso)


def compute_provenance_weight(
    record: ProvenanceRecord,
    *,
    base_weight: float = 1.0,
    max_boost: float = 0.3,
) -> float:
    """Weight retrieval results by provenance chain depth.

    Facts retrieved multiple times from diverse sources receive
    higher weight. Single-source, low-retrieval facts get base weight.
    """
    if record.retrieval_count <= 1:
        return base_weight

    # Diversity bonus: more unique sources = stronger provenance
    unique_sources = len(set(record.sources))
    diversity_bonus = min(max_boost, unique_sources * 0.05)

    # Recency bonus: facts retrieved recently get slight boost
    recency_bonus: float = 0.0
    if record.last_retrieved:
        try:
            last = datetime.fromisoformat(record.last_retrieved)
            hours_since = (datetime.now(timezone.utc) - last).total_seconds() / 3600
            if hours_since < 24:
                recency_bonus = 0.05 * (1.0 - hours_since / 24)
        except (ValueError, TypeError):
            pass

    return round(min(base_weight + diversity_bonus + recency_bonus, 1.5), 4)


# ── Retrieval score composer ──────────────────────────────────────────────


def make_retrieval_scorer(
    *,
    source_weights: dict[str, float] | None = None,
    event_type_weights: dict[str, float] | None = None,
    signal_terms: dict[str, float] | None = None,
) -> "ScorerCallable":
    """Factory: return a scorer function for TfidfIndex.search().

    The scorer blends TF-IDF cosine similarity with salience scoring.
    """

    src_w = source_weights or DEFAULT_SOURCE_WEIGHTS
    evt_w = event_type_weights or DEFAULT_EVENT_TYPE_WEIGHTS
    sig_t = signal_terms or DEFAULT_SIGNAL_TERMS

    def scorer(entry: IndexEntry, query_tf: dict[str, float], base_similarity: float) -> float:
        salience = compute_salience(
            entry,
            source_weights=src_w,
            event_type_weights=evt_w,
            signal_terms=sig_t,
        )
        # Blend: 70% TF-IDF similarity, 30% salience
        return base_similarity * 0.7 + salience * 0.3

    return scorer


# Type alias for the scorer signature
from typing import Protocol


class ScorerCallable(Protocol):
    def __call__(self, entry: IndexEntry, query_tf: dict[str, float], base_similarity: float) -> float: ...
