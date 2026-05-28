"""Knowledge synthesis — LLM-driven bridge description. Fully optional.

When OLLAMA_HOST is configured, calls Ollama to generate a one-sentence
description of the latent relationship between modules that share concepts.
Without an LLM, produces a deterministic fallback. Times out gracefully
after 5 seconds.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING

from core.fusion.bridge_detector import BridgeCandidate

if TYPE_CHECKING:
    from core.fusion.concept_graph import ConceptGraph


@dataclass
class SynthesisResult:
    """A synthesized description of a cross-module bridge."""

    bridge: BridgeCandidate
    synthesis_text: str              # LLM output or fallback description
    llm_available: bool              # True if LLM was actually called
    generated_at: float


class BridgeSynthesizer:
    """Generate descriptions of cross-module bridges.

    Uses Ollama HTTP API (stdlib only — no requests/httpx).
    Degrades gracefully: timeout or unavailable LLM → fallback text.
    """

    def __init__(self, ollama_host: str | None = None) -> None:
        self._ollama_host = ollama_host or os.environ.get("OLLAMA_HOST") or os.environ.get(
            "CENTROID_OLLAMA_URL", ""
        )
        self._model = os.environ.get("CENTROID_OLLAMA_MODEL", "phi4-mini:latest")

    def synthesize(
        self,
        bridge: BridgeCandidate,
        concept_graph: ConceptGraph,
    ) -> SynthesisResult:
        """Synthesize a description of the bridge.

        If LLM is available: prompt it to describe the latent relationship.
        If not: produce a deterministic fallback.
        """
        shared_concepts = sorted(
            concept_graph.module_index.get(bridge.module_a, set())
            & concept_graph.module_index.get(bridge.module_b, set())
        )

        if self._ollama_host:
            text, llm_ok = self._call_ollama(bridge, shared_concepts)
        else:
            llm_ok = False
            text = ""

        if not llm_ok:
            text = (
                f"Modules '{bridge.module_a}' and '{bridge.module_b}' "
                f"share {bridge.shared_concept_count} concepts including: "
                f"{', '.join(shared_concepts[:3])}."
            )

        return SynthesisResult(
            bridge=bridge,
            synthesis_text=text,
            llm_available=llm_ok,
            generated_at=time.time(),
        )

    def synthesize_all(
        self,
        bridges: list[BridgeCandidate],
        concept_graph: ConceptGraph,
        max_bridges: int = 5,
    ) -> list[SynthesisResult]:
        """Process top N bridges by bridge_score."""
        top = sorted(bridges, key=lambda b: b.bridge_score, reverse=True)[:max_bridges]
        return [self.synthesize(b, concept_graph) for b in top]

    # ── Internal ──────────────────────────────────────────────────────────

    def _call_ollama(self, bridge: BridgeCandidate, concepts: list[str]) -> tuple[str, bool]:
        """Call Ollama HTTP API. Returns (text, success)."""
        prompt = (
            f"Module '{bridge.module_a}' and module '{bridge.module_b}' "
            f"share these concepts: {', '.join(concepts[:5])}.\n"
            f"In one sentence, describe the latent architectural relationship "
            f"between them."
        )

        payload = json.dumps({
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"num_predict": 64, "temperature": 0.3},
        }).encode("utf-8")

        url = f"{self._ollama_host.rstrip('/')}/api/chat"
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                msg = data.get("message", {})
                content = msg.get("content", "") or msg.get("thinking", "")
                if content:
                    return content.strip(), True
        except (OSError, ValueError, json.JSONDecodeError):
            return "", False

        return "", False
