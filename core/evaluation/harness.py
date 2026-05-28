from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from core.resources import read_text_resource_or_file

from .metrics import MetricResult, clamp_score
from . import probes as _expanded_probe_module
from .probes import (
    action_correction_probe,
    config_audit_provenance_probe,
    configured_agent_cli_execution_probe,
    configured_memory_retention_variation_probe,
    configured_priority_route_variation_probe,
    configured_safety_outcome_variation_probe,
    continuity_probe,
    distributed_coordination_probe,
    holly_backward_compatibility_probe,
    holly_config_load_probe,
    holly_identity_drift_stability_probe,
    holly_project_state_restore_probe,
    holly_safety_gate_enforcement_probe,
    holly_template_customization_probe,
    holly_temporal_reconciliation_probe,
    memory_drift_probe,
    memory_probe,
    mock_provider_runtime_execution_probe,
    model_adapter_contract_normalization_probe,
    model_tool_proposal_safety_gate_probe,
    priority_probe,
    provider_audit_secret_redaction_probe,
    provider_capability_enforcement_probe,
    provider_cli_mock_execution_probe,
    reconciliation_probe,
    routing_probe,
    safety_probe,
    self_model_probe,
    temporal_probe,
)

EXPANDED_PROBE_NAMES = (
    "memory_append_tail_compat",
    "memory_search_returns_results",
    "memory_search_relevance_ordering",
    "memory_pyramid_tier_assignment",
    "memory_compact_evicts_lowest",
    "memory_index_rebuilds_on_init",
    "self_model_health_ratio_bounds",
    "self_model_status_reflects_ratio",
    "self_model_tick_produces_snapshot",
    "self_model_anomaly_detection_fires",
    "self_model_fault_tolerant_collect",
    "self_model_backward_compat_no_sources",
    "coherence_graph_loads_yaml",
    "coherence_propagation_clamped",
    "coherence_suppresses_edge",
    "coherence_index_scalar_bounds",
    "coherence_tick_writes_snapshot",
    "coherence_simulate_no_disk_write",
    "planner_forecast_three_horizons",
    "planner_forecast_ids_unique",
    "planner_calibration_updates_mae",
    "planner_calibration_persists",
    "planner_thread_lifecycle",
    "planner_feedback_resolves",
    "simulation_fork_isolated",
    "simulation_intervention_applies",
    "simulation_divergence_zero",
    "simulation_preflight_escalates",
    "simulation_preflight_no_disk_write",
    "sensory_code_encoder_extracts",
    "sensory_telemetry_qualifiers",
    "sensory_encoder_truncates",
    "sensory_projector_similarity_self",
    "sensory_pipeline_startup_scan",
    "fusion_concept_graph_builds",
    "fusion_stopwords_filtered",
    "fusion_bridge_detector_finds",
    "fusion_bridge_score_bounds",
    "fusion_synthesis_fallback",
)

PROBES = {
    "action_correction": action_correction_probe,
    "config_audit_provenance": config_audit_provenance_probe,
    "configured_agent_cli_execution": configured_agent_cli_execution_probe,
    "configured_memory_retention_variation": configured_memory_retention_variation_probe,
    "configured_priority_route_variation": configured_priority_route_variation_probe,
    "configured_safety_outcome_variation": configured_safety_outcome_variation_probe,
    "continuity": continuity_probe,
    "distributed_coordination": distributed_coordination_probe,
    "holly_config_load": holly_config_load_probe,
    "holly_backward_compatibility": holly_backward_compatibility_probe,
    "holly_identity_drift_stability": holly_identity_drift_stability_probe,
    "holly_project_state_restore": holly_project_state_restore_probe,
    "holly_safety_gate_enforcement": holly_safety_gate_enforcement_probe,
    "holly_template_customization": holly_template_customization_probe,
    "holly_temporal_reconciliation": holly_temporal_reconciliation_probe,
    "provider_cli_mock_execution": provider_cli_mock_execution_probe,
    "memory": memory_probe,
    "memory_drift": memory_drift_probe,
    "mock_provider_runtime_execution": mock_provider_runtime_execution_probe,
    "model_adapter_contract_normalization": model_adapter_contract_normalization_probe,
    "model_tool_proposal_safety_gate": model_tool_proposal_safety_gate_probe,
    "priority": priority_probe,
    "provider_audit_secret_redaction": provider_audit_secret_redaction_probe,
    "provider_capability_enforcement": provider_capability_enforcement_probe,
    "reconciliation": reconciliation_probe,
    "routing": routing_probe,
    "safety": safety_probe,
    "self_model": self_model_probe,
    "temporal": temporal_probe,
}

PROBES.update(
    {
        probe_name: getattr(_expanded_probe_module, f"{probe_name}_probe")
        for probe_name in EXPANDED_PROBE_NAMES
    }
)


@dataclass(frozen=True)
class EvaluationReport:
    suite_name: str
    score: float
    passed: bool
    results: list[MetricResult]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["results"] = [result.to_dict() for result in self.results]
        return data


class EvaluationHarness:
    def __init__(self, minimum_score: float = 0.85):
        self.minimum_score = minimum_score

    def run_file(self, fixture_path: Path) -> EvaluationReport:
        fixture = json.loads(read_text_resource_or_file(fixture_path))
        return self.run_fixture(fixture)

    def run_fixture(self, fixture: dict) -> EvaluationReport:
        results: list[MetricResult] = []
        for probe_name, cases in fixture.get("probes", {}).items():
            if probe_name not in PROBES:
                raise ValueError(f"unknown evaluation probe: {probe_name}")
            results.append(PROBES[probe_name](cases))

        score = self._weighted_score(results)
        return EvaluationReport(
            suite_name=fixture.get("suite_name", "unnamed"),
            score=score,
            passed=score >= self.minimum_score and all(result.passed for result in results),
            results=results,
        )

    @staticmethod
    def _weighted_score(results: list[MetricResult]) -> float:
        if not results:
            return 0.0
        return clamp_score(sum(result.score for result in results) / len(results))
