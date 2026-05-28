"""Centroid memory layer: event persistence, semantic search, and tiered compaction."""

from core.memory.embedding_cache import cached_embed, cache_stats, clear_cache, set_embedding_provider
from core.memory.memory_pyramid import MemoryPyramid, TierCapacity, TierDecision
from core.memory.retrieval import (
    ProvenanceRecord,
    compute_provenance_weight,
    compute_salience,
    make_retrieval_scorer,
)
from core.memory.store import Event, MemoryStore, SearchResult
from core.memory.tfidf_index import IndexEntry, TfidfIndex

__all__ = [
    # Store
    "Event",
    "MemoryStore",
    "SearchResult",
    # TF-IDF
    "TfidfIndex",
    "IndexEntry",
    # Retrieval
    "compute_salience",
    "compute_provenance_weight",
    "ProvenanceRecord",
    "make_retrieval_scorer",
    # Pyramid
    "MemoryPyramid",
    "TierCapacity",
    "TierDecision",
    # Embedding cache
    "cached_embed",
    "cache_stats",
    "clear_cache",
    "set_embedding_provider",
]
