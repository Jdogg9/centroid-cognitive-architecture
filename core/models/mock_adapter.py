from __future__ import annotations

import time

from .base import ModelAdapter
from .types import ModelRequest, ModelResponse, ModelToolProposal


class MockModelAdapter(ModelAdapter):
    capability_path = "mock_fixture"

    def generate(self, request: ModelRequest) -> ModelResponse:
        started = time.perf_counter()
        scenario = request.scenario_id or "default"
        text = self._text_for_scenario(scenario)
        proposals: list[ModelToolProposal] = []
        if scenario in {"tool-proposal", "operations-observer", "safety-gate"}:
            proposals.append(
                ModelToolProposal.create(
                    proposal_id="mock-proposal-restart-service",
                    name="restart_service",
                    arguments={
                        "resource": "checkout-worker",
                        "intended_effect": "restart service checkout-worker",
                        "risk_level": "high",
                        "reversible": True,
                        "mutates_state": True,
                    },
                    provider_id=self.provider_id,
                    model_id=self.model_id,
                )
            )
        latency = self._elapsed_ms(started)
        audit = self._audit(request, latency_ms=latency, tool_count=len(proposals))
        return ModelResponse(
            text=text,
            tool_proposals=proposals,
            provider_id=self.provider_id,
            model_id=self.model_id,
            usage={
                "input_tokens": sum(len(m.content.split()) for m in request.messages),
                "output_tokens": len(text.split()),
            },
            latency_ms=latency,
            finish_reason="stop",
            capabilities=self.capabilities(),
            provider_metadata={"fixture": scenario},
            audit=audit,
        )

    def _text_for_scenario(self, scenario: str) -> str:
        if scenario == "tool-proposal":
            return "Centroid mock provider proposes a bounded operational action for safety review."
        if scenario == "project-companion":
            return (
                "Centroid mock provider restored project context while "
                "preserving configured constraints."
            )
        return "Centroid mock provider produced deterministic text through the provider contract."
