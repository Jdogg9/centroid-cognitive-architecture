"""Latent projector — cross-modal similarity search over PerceivedText.

Shares the TF-IDF vector space with the core/memory module. Code,
telemetry, and sensory observations can be compared via cosine similarity
in the same sparse vector space. No new vector implementation needed.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from core.memory.tfidf_index import (
    TfidfIndex,
    compute_tf,
    sparse_cosine,
    tokenize,
)
from nodes.sensory_node import PerceivedText
from nodes.sensory_node.code_encoder import CodeEncoder

if TYPE_CHECKING:
    from core.memory.store import MemoryStore


class LatentProjector:
    """Cross-modal perceptual similarity engine."""

    def __init__(self, index: TfidfIndex | None = None) -> None:
        self._index = index or TfidfIndex()
        self._doc_ids: set[str] = set()

    def add(self, perceived: PerceivedText) -> None:
        """Index a PerceivedText for search."""
        self._index.add(
            doc_id=perceived.source_id,
            text=perceived.content,
            source=perceived.source_kind,
        )
        self._doc_ids.add(perceived.source_id)
        self._index.recompute_idf()

    def add_batch(self, perceived_list: list[PerceivedText]) -> None:
        """Index multiple PerceivedTexts."""
        for perceived in perceived_list:
            self._index.add(
                doc_id=perceived.source_id,
                text=perceived.content,
                source=perceived.source_kind,
            )
            self._doc_ids.add(perceived.source_id)
        self._index.recompute_idf()

    def similarity(self, a: PerceivedText, b: PerceivedText) -> float:
        """Return cosine similarity between two PerceivedTexts.

        Both must have been add()-ed first.
        Raises KeyError if either source_id is missing from the index.
        """
        if a.source_id not in self._doc_ids:
            raise KeyError(f"source_id '{a.source_id}' not in index — call add() first")
        if b.source_id not in self._doc_ids:
            raise KeyError(f"source_id '{b.source_id}' not in index — call add() first")

        # Compute TF-IDF vectors via the index's internal IDF from all entries
        from core.memory.tfidf_index import compute_idf

        all_tokens = [entry.tokens for entry in self._index.entries]
        idf = compute_idf(all_tokens)

        a_tokens = tokenize(a.content)
        b_tokens = tokenize(b.content)

        a_tf = compute_tf(a_tokens)
        b_tf = compute_tf(b_tokens)

        a_vec: dict[str, float] = {t: tf_val * idf.get(t, 1.0) for t, tf_val in a_tf.items()}
        b_vec: dict[str, float] = {t: tf_val * idf.get(t, 1.0) for t, tf_val in b_tf.items()}

        return round(sparse_cosine(a_vec, b_vec), 6)

    def search(self, query_text: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Search for PerceivedTexts similar to query_text.

        Returns [(source_id, score)] sorted by descending similarity.
        """
        results = self._index.search(query_text, top_k=top_k)
        return [(entry.doc_id, score) for entry, score in results]

    def cross_modal_search(
        self, perceived: PerceivedText, top_k: int = 5
    ) -> list[tuple[str, float]]:
        """Find PerceivedTexts from any modality similar to this one."""
        return self.search(perceived.content, top_k=top_k)


class SensoryPipeline:
    """Convenience orchestrator for initial module scan and perception."""

    def __init__(
        self,
        core_root: str | Path = "core/",
        memory_store: MemoryStore | None = None,
    ) -> None:
        self._core_root = Path(core_root)
        self._memory_store = memory_store
        self._code_encoder = CodeEncoder()
        self._projector = LatentProjector()

    @property
    def projector(self) -> LatentProjector:
        return self._projector

    def run_startup_scan(self) -> list[PerceivedText]:
        """Scan all core modules and index their code structure.

        Returns the list of PerceivedText produced.
        If memory_store is configured, emits sensory_perception events.
        """
        perceived_list = self._code_encoder.encode_directory(self._core_root)
        self._projector.add_batch(perceived_list)

        if self._memory_store is not None:
            from core.memory.store import Event

            for perceived in perceived_list:
                self._memory_store.append(
                    Event(
                        event_type="sensory_perception",
                        content=perceived.content,
                        source="sensory_pipeline",
                        metadata={
                            "classification": "sensory",
                            "source_kind": perceived.source_kind,
                            "source_id": perceived.source_id,
                            "content_length": str(len(perceived.content)),
                        },
                    )
                )

        return perceived_list
