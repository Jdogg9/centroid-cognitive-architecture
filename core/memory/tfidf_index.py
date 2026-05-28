"""TF-IDF index for semantic search over JSONL event stores.

Pure Python — zero dependencies beyond stdlib. Designed to index Centroid's
append-only MemoryStore for cosine-similarity recall without requiring an
external vector database.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from math import log, sqrt
from typing import Callable


# ── Stop words ────────────────────────────────────────────────────────────

STOP_WORDS: set[str] = set(
    "the a an and or but in on at to for of with is are was were be "
    "been being have has had do does did will would shall should may "
    "might must can could it its they them their we us our you your "
    "he she his her this that these those from by as if not no so all "
    "any each every both few many much some such".split()
)


# ── Tokenizer ─────────────────────────────────────────────────────────────


def tokenize(text: str) -> list[str]:
    """Lowercase, extract word tokens, remove stop words and short tokens."""
    tokens: list[str] = re.findall(r"\b[a-z]{2,}\b", text.lower())
    return [t for t in tokens if t not in STOP_WORDS]


# ── Term frequency / inverse document frequency ───────────────────────────


def compute_tf(tokens: list[str]) -> dict[str, float]:
    """Log-normalized term frequency."""
    count = Counter(tokens)
    total = len(tokens) or 1
    return {term: log(1 + freq / total) for term, freq in count.items()}


def compute_idf(documents: list[list[str]]) -> dict[str, float]:
    """Inverse document frequency over a corpus."""
    n_docs = len(documents)
    df: Counter[str] = Counter()
    for doc in documents:
        df.update(set(doc))
    return {term: log((n_docs + 1) / (freq + 1)) + 1 for term, freq in df.items()}


# ── Sparse cosine similarity ──────────────────────────────────────────────


def sparse_cosine(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Cosine similarity between two {term: weight} sparse vectors."""
    common = set(vec_a) & set(vec_b)
    dot = sum(vec_a[k] * vec_b[k] for k in common)
    mag_a = sqrt(sum(v * v for v in vec_a.values()))
    mag_b = sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Dense cosine similarity (for embedding vectors) ───────────────────────


def dense_cosine(vec_a: list[float] | None, vec_b: list[float] | None) -> float:
    """Cosine similarity between two dense float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = sqrt(sum(a * a for a in vec_a))
    mag_b = sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Index entry ────────────────────────────────────────────────────────────


@dataclass
class IndexEntry:
    """A single indexed document in the TF-IDF store."""

    doc_id: str
    text: str
    source: str = "unknown"
    tokens: list[str] = field(default_factory=list)
    tf: dict[str, float] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


# ── TF-IDF Index ───────────────────────────────────────────────────────────


class TfidfIndex:
    """Sparse TF-IDF index for semantic search over documents.

    Call build_from_entries when the underlying store changes. Documents
    are indexed as (doc_id, text) tuples. The index lazily recomputes
    IDF on each search to handle incremental additions efficiently.
    """

    def __init__(self) -> None:
        self._entries: list[IndexEntry] = []
        self._idf: dict[str, float] = {}

    @property
    def entries(self) -> list[IndexEntry]:
        return list(self._entries)

    @property
    def size(self) -> int:
        return len(self._entries)

    def add(self, doc_id: str, text: str, *, source: str = "unknown", metadata: dict | None = None) -> IndexEntry:
        """Index a single document. Recomputes IDF lazily — call
        recompute_idf() before search if recency matters."""
        tokens = tokenize(text)
        entry = IndexEntry(
            doc_id=doc_id,
            text=text,
            source=source,
            tokens=tokens,
            tf=compute_tf(tokens),
            metadata=metadata or {},
        )
        self._entries.append(entry)
        # Incrementally update IDF
        for token in set(tokens):
            self._idf[token] = self._idf.get(token, 0) + 1
        return entry

    def recompute_idf(self) -> None:
        """Recalculate IDF from all currently indexed entries."""
        docs = [entry.tokens for entry in self._entries]
        self._idf = compute_idf(docs)

    def search(
        self,
        query: str,
        top_k: int = 5,
        *,
        scorer: Callable[[IndexEntry, dict[str, float], float], float] | None = None,
    ) -> list[tuple[IndexEntry, float]]:
        """Search the index with a text query.

        Returns top_k (entry, score) tuples sorted by similarity (descending).
        If scorer is provided, it's called as scorer(entry, query_tf, base_similarity)
        and should return a final adjusted score.
        """
        if not self._entries:
            return []

        query_tokens = tokenize(query)
        query_tf = compute_tf(query_tokens)

        # Build query TF-IDF vector
        query_vec: dict[str, float] = {}
        for term, tf_val in query_tf.items():
            idf_val = self._idf.get(term, 1.0)
            query_vec[term] = tf_val * idf_val

        # Build TF-IDF vector for each entry and score
        scored: list[tuple[IndexEntry, float]] = []
        for entry in self._entries:
            entry_vec: dict[str, float] = {}
            for term, tf_val in entry.tf.items():
                idf_val = self._idf.get(term, 1.0)
                entry_vec[term] = tf_val * idf_val

            base_score = sparse_cosine(query_vec, entry_vec)

            if scorer is not None:
                final_score = scorer(entry, query_tf, base_score)
            else:
                final_score = base_score

            if final_score > 0.0:
                scored.append((entry, round(final_score, 6)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def clear(self) -> None:
        """Remove all indexed entries."""
        self._entries.clear()
        self._idf.clear()
