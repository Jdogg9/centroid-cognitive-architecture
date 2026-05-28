# Architecture Reference — v0.7.0

Centroid Cognitive Architecture v0.7.0 is a seven-layer, stdlib-first reference implementation. This document is a concise implementation reference: file layout, dependency graph, state files, environment variables, coherence edge semantics, and probe index.

## 1. Repository Structure

```text
centroid-cognitive-architecture/
├── README.md
├── pyproject.toml
├── config/
│   └── coherence_graph.yaml
├── configs/
│   ├── holly/{base,operations_observer,project_companion,support_continuity}.json
│   └── providers/{mock,openai,anthropic,ollama,vllm}.json.example
├── core/
│   ├── agent_config.py
│   ├── identity/model.py
│   ├── memory/{store,tfidf_index,retrieval,memory_pyramid,embedding_cache}.py
│   ├── self_model/{model,telemetry_aggregator,health_scorer,anomaly_detector,world_snapshot}.py
│   ├── coherence/{graph_loader,propagation,coherence_index,do_operator,coherence_graph}.py
│   ├── planner/{planner,forecast,calibration,plan_tree,feedback_loop}.py
│   ├── simulation/{twin_buffer,intervention,divergence,safety_preflight}.py
│   ├── fusion/{concept_graph,bridge_detector,synthesis}.py
│   ├── models/{base,types,registry,mock_adapter,openai_adapter,anthropic_adapter,openai_compatible_adapter,capabilities,errors}.py
│   ├── runtime/{configured_agent,configured_memory,configured_priority,configured_safety,audit,cli}.py
│   ├── priority/scoring.py
│   ├── router/router.py
│   ├── safety/policy.py
│   ├── temporal/metrics.py
│   └── evaluation/{harness,metrics,probes,cli}.py
├── nodes/
│   ├── sensory_node/{__init__,code_encoder,telemetry_encoder,sensory_encoder,latent_projector}.py
│   ├── reflex_node/README.md
│   ├── deliberation_node/README.md
│   ├── memory_node/README.md
│   └── orchestration_node/README.md
├── schemas/
│   ├── agent_config.schema.json
│   ├── evaluation_result.schema.json
│   ├── memory_event.schema.json
│   ├── message_event.schema.json
│   ├── model_provider.schema.json
│   ├── node_heartbeat.schema.json
│   ├── safety_decision.schema.json
│   └── telemetry_event.schema.json
├── evaluation/fixtures/baseline.json
├── examples/
│   ├── run_demo.py
│   ├── run_evaluation.py
│   ├── run_holly.py
│   ├── run_agent.py
│   ├── run_config_comparison.py
│   ├── run_provider_demo.py
│   ├── run_provider_comparison.py
│   ├── run_identity_demo.py
│   └── run_temporal_demo.py
├── tests/
│   ├── coherence/test_coherence.py
│   ├── fusion/test_fusion.py
│   ├── memory/test_memory_search.py and schema/drift/example tests
│   ├── planner/test_forecast.py
│   ├── self_model/test_telemetry.py and contract tests
│   ├── sensory_node/test_sensory.py
│   ├── distributed/, identity/, safety/, temporal/
│   └── top-level demo, provider, benchmark, installability, and runtime tests
├── benchmarks/
├── templates/
└── docs/
```

## 2. Module Dependency Graph

```text
nodes/sensory_node/code_encoder.py -> nodes.sensory_node.PerceivedText
nodes/sensory_node/telemetry_encoder.py -> nodes.sensory_node.PerceivedText
nodes/sensory_node/sensory_encoder.py -> nodes.sensory_node.PerceivedText
nodes/sensory_node/latent_projector.py -> core.memory.tfidf_index, core.memory.store, CodeEncoder

core/memory/store.py -> core.memory.tfidf_index, core.memory.retrieval, core.memory.memory_pyramid
core/memory/retrieval.py -> core.memory.tfidf_index
core/memory/embedding_cache.py -> optional Ollama-compatible environment

core/self_model/model.py -> telemetry_aggregator, health_scorer, anomaly_detector, world_snapshot, core.memory.store
core/self_model/world_snapshot.py -> state/world_snapshot.json, state/world_trends.json

core/coherence/coherence_graph.py -> graph_loader, propagation, coherence_index, do_operator, core.self_model.world_snapshot
core/coherence/propagation.py -> graph_loader
core/coherence/do_operator.py -> graph_loader, propagation

core/planner/forecast.py -> core.planner.calibration
core/planner/feedback_loop.py -> forecast, calibration, plan_tree
core/planner/plan_tree.py -> state/plan_tree.json
core/planner/calibration.py -> state/calibration.json

core/simulation/twin_buffer.py -> state/world_snapshot.json
core/simulation/intervention.py -> twin state dictionaries
core/simulation/divergence.py -> simulated and baseline trajectories
core/simulation/safety_preflight.py -> divergence, intervention, core.safety.policy

core/fusion/concept_graph.py -> nodes.sensory_node.PerceivedText
core/fusion/bridge_detector.py -> concept_graph, optional core.coherence.graph_loader.CoherenceGraphDef
core/fusion/synthesis.py -> bridge_detector, concept_graph, urllib.request, Ollama-compatible environment

core/runtime/configured_agent.py -> agent_config, configured_priority, configured_safety, configured_memory, models, safety, memory, router
examples/run_demo.py -> identity, memory, priority, router, safety, self_model, evaluation harness
```

## 3. State Files

| File | Written by | Read by | Format |
|---|---|---|---|
| `state/world_snapshot.json` | `world_snapshot.py` | `coherence_graph.py`, `twin_buffer.py` | JSON |
| `state/world_trends.json` | `world_snapshot.py` | reference only | JSON |
| `state/calibration.json` | `calibration.py` | `forecast.py`, `feedback_loop.py` | JSON |
| `state/plan_tree.json` | `plan_tree.py` | `feedback_loop.py` | JSON |

## 4. Environment Variables

| Variable | Module | Effect |
|---|---|---|
| `OLLAMA_HOST` | `embedding_cache.py`, `synthesis.py` | Activates optional Ollama-compatible embedding or bridge-synthesis paths |
| `CENTROID_OLLAMA_URL` | `embedding_cache.py`, `synthesis.py` | Alternative Ollama-compatible host URL |
| `CENTROID_OLLAMA_MODEL` | `synthesis.py` | Bridge synthesis model name, default `phi4-mini:latest` |

Provider examples also document provider-specific variables such as `CENTROID_OPENAI_API_KEY`, but the seven-layer v0.7.0 runtime additions above only require the variables listed in this table for optional LLM paths.

## 5. Edge Type Reference

The coherence graph accepts seven edge types:

| Edge type | Propagation semantics |
|---|---|
| `multiplicative_factor` | Downstream value becomes `upstream * weight`; used when upstream health directly scales downstream health. |
| `proportional` | Same numeric semantics as `multiplicative_factor`; used for readable graph intent when influence is proportional. |
| `modulates` | Same numeric semantics as `multiplicative_factor`; used when upstream state gates or shapes downstream behavior. |
| `additive_factor` | Downstream value becomes `downstream + upstream * weight`; used for positive additive support. |
| `reinforces` | Same numeric semantics as `additive_factor`; used when upstream reinforces downstream stability. |
| `suppresses` | Downstream value becomes `downstream * (1.0 - upstream * weight)`; used for inhibitory or risk-reducing influence. |
| `feedback` | Applied after the topological pass as `downstream + (upstream - 0.5) * weight * 0.05`; excluded from Kahn sorting to avoid cycles. |

All propagated outputs are clamped to `[0.0, 1.0]`.

## 6. Evaluation Probe Index

All probes below pass at v0.7.0.

### test_coherence.py (18 PASS)
- PASS `test_graph_loader_valid`
- PASS `test_graph_loader_unknown_edge_type`
- PASS `test_graph_loader_undeclared_node`
- PASS `test_graph_loader_weight_bounds`
- PASS `test_propagation_output_clamped`
- PASS `test_propagation_suppresses_reduces`
- PASS `test_propagation_reinforces_increases`
- PASS `test_propagation_feedback_not_in_topo_order`
- PASS `test_propagation_neutral_default`
- PASS `test_do_operator_severs_inbound`
- PASS `test_do_operator_compare_delta`
- PASS `test_coherence_index_bounds`
- PASS `test_coherence_report_weakest_strongest`
- PASS `test_coherence_graph_tick_returns_report`
- PASS `test_coherence_graph_ticks_are_consistent`
- PASS `test_coherence_graph_reload_config`
- PASS `test_coherence_graph_simulate_no_write`
- PASS `test_coherence_graph_tick_writes_snapshot`

### test_distributed_coordination_probe.py (1 PASS)
- PASS `test_distributed_coordination_probe`

### test_node_and_message_schemas.py (2 PASS)
- PASS `test_node_heartbeat_schema`
- PASS `test_message_event_schema`

### test_schema_examples.py (1 PASS)
- PASS `test_distributed_schema_examples_are_valid`

### test_fusion.py (11 PASS)
- PASS `test_concept_graph_builds`
- PASS `test_concept_graph_multi_module`
- PASS `test_concept_graph_stopword_filtered`
- PASS `test_concept_graph_frequency_filter`
- PASS `test_concept_graph_top_concepts`
- PASS `test_bridge_detector_finds_shared`
- PASS `test_bridge_detector_no_self_pairs`
- PASS `test_bridge_detector_score_bounds`
- PASS `test_bridge_detector_implicit_filter`
- PASS `test_synthesis_fallback_no_llm`
- PASS `test_synthesis_llm_available_flag`

### test_identity_continuity.py (3 PASS)
- PASS `test_identity_drift_is_zero_for_stable_state`
- PASS `test_identity_drift_detects_changed_agent_id`
- PASS `test_identity_evolution_versions_state`

### test_memory_drift_probe.py (1 PASS)
- PASS `test_memory_drift_probe`

### test_memory_event_schema.py (1 PASS)
- PASS `test_memory_store_roundtrip_and_schema`

### test_memory_examples.py (1 PASS)
- PASS `test_memory_example_is_valid`

### test_memory_search.py (13 PASS)
- PASS `test_tfidf_index_search_exact`
- PASS `test_tfidf_index_no_results`
- PASS `test_tfidf_index_empty`
- PASS `test_memory_store_search_and_schema`
- PASS `test_memory_store_search_provenance_tracking`
- PASS `test_compute_salience_high_for_decision`
- PASS `test_compute_salience_low_for_plain_observation`
- PASS `test_memory_pyramid_tier_classification`
- PASS `test_memory_pyramid_compaction_retains_most`
- PASS `test_memory_pyramid_compaction_evicts_under_tight_capacity`
- PASS `test_memory_store_compact_delegates`
- PASS `test_memory_store_tier_counts`
- PASS `test_memory_store_original_api_preserved`

### test_forecast.py (19 PASS)
- PASS `test_plan_step_backward_compat`
- PASS `test_forecast_generates_three_horizons`
- PASS `test_forecast_confidence_cold_start`
- PASS `test_forecast_id_unique`
- PASS `test_forecast_predictions_approach_current_over_time`
- PASS `test_calibration_update_incremental`
- PASS `test_calibration_bias_signed`
- PASS `test_calibration_persists_to_disk`
- PASS `test_calibration_load_roundtrip`
- PASS `test_calibration_all_records`
- PASS `test_plan_tree_add_active`
- PASS `test_plan_tree_abandon_threshold`
- PASS `test_plan_tree_complete`
- PASS `test_plan_tree_active_filter`
- PASS `test_plan_tree_all_threads`
- PASS `test_feedback_loop_register_resolve`
- PASS `test_feedback_loop_calibration_updated`
- PASS `test_feedback_loop_medium_delayed`
- PASS `test_feedback_loop_confidence_update`

### test_policy_fixture.py (2 PASS)
- PASS `test_safety_example_is_valid`
- PASS `test_safety_policy_fixture_matches_reference_logic`

### test_safety_invariants.py (3 PASS)
- PASS `test_mutating_action_requires_approval`
- PASS `test_destructive_action_denied_even_when_confirmed`
- PASS `test_safety_decision_schema`

### test_self_model_contract.py (2 PASS)
- PASS `test_self_model_status_classification`
- PASS `test_non_claims_are_explicit`

### test_telemetry.py (24 PASS)
- PASS `test_telemetry_aggregator_collect`
- PASS `test_telemetry_aggregator_fault_tolerance`
- PASS `test_telemetry_aggregator_no_sources`
- PASS `test_health_scorer_score_bounds`
- PASS `test_health_scorer_clips_out_of_range`
- PASS `test_health_scorer_trend_direction`
- PASS `test_health_scorer_trend_negative`
- PASS `test_health_scorer_system_ratio`
- PASS `test_health_scorer_system_ratio_empty`
- PASS `test_health_scorer_all_health`
- PASS `test_anomaly_detector_cold_start`
- PASS `test_anomaly_detector_z_score_warn`
- PASS `test_anomaly_detector_z_score_critical`
- PASS `test_anomaly_detector_no_false_positives`
- PASS `test_world_snapshot_write_read_roundtrip`
- PASS `test_world_snapshot_atomic_write`
- PASS `test_world_snapshot_read_missing`
- PASS `test_self_model_backward_compat_health_ratio`
- PASS `test_self_model_snapshot_preserved`
- PASS `test_self_model_tick_emits_snapshot`
- PASS `test_self_model_anomaly_appended`
- PASS `test_self_model_status_healthy`
- PASS `test_self_model_status_degraded`
- PASS `test_self_model_multiple_ticks_trend`

### test_sensory.py (15 PASS)
- PASS `test_code_encoder_extracts_signatures`
- PASS `test_code_encoder_extracts_docstrings`
- PASS `test_code_encoder_missing_file`
- PASS `test_code_encoder_skips_non_python`
- PASS `test_code_encoder_directory_walk`
- PASS `test_telemetry_encoder_high_low_labels`
- PASS `test_telemetry_encoder_snapshot`
- PASS `test_sensory_encoder_flat`
- PASS `test_sensory_encoder_nested`
- PASS `test_sensory_encoder_truncation`
- PASS `test_latent_projector_similarity_self`
- PASS `test_latent_projector_cross_modal`
- PASS `test_latent_projector_search_returns_sorted`
- PASS `test_sensory_pipeline_startup_scan`
- PASS `test_sensory_pipeline_memory_append`

### test_reconciliation_and_correction.py (1 PASS)
- PASS `test_reconciliation_and_action_correction_probes`

### test_telemetry_event_schema.py (1 PASS)
- PASS `test_latency_metric_and_telemetry_schema`

### test_telemetry_examples.py (1 PASS)
- PASS `test_telemetry_example_is_valid`

### test_additional_demos.py (1 PASS)
- PASS `test_additional_demos_pass`

### test_benchmarks.py (2 PASS)
- PASS `test_benchmarks_pass`
- PASS `test_run_all_benchmarks`

### test_configured_runtime.py (8 PASS)
- PASS `test_config_inheritance_and_overrides_apply_to_holly_profile`
- PASS `test_invalid_config_threshold_raises_helpful_error`
- PASS `test_priority_policy_changes_route_for_same_signal`
- PASS `test_safety_policy_changes_outcome_for_same_request`
- PASS `test_memory_policy_changes_retained_records_and_redacts_sensitive_fields`
- PASS `test_audit_records_include_config_provenance`
- PASS `test_configured_agent_cli_runs_from_template`
- PASS `test_config_comparison_demo_shows_different_config_outcomes`

### test_demo.py (4 PASS)
- PASS `test_demo_components`
- PASS `test_full_demo_passes`
- PASS `test_minimal_demo_passes`
- PASS `test_demo_evaluation_passes`

### test_evaluation.py (3 PASS)
- PASS `test_baseline_fixture_passes`
- PASS `test_unknown_probe_rejected`
- PASS `test_evaluation_report_schema`

### test_holly.py (11 PASS)
- PASS `test_holly_configs_load_and_preserve_required_boundaries`
- PASS `test_holly_configs_validate_against_schema`
- PASS `test_minimal_agent_template_validates_and_customizes`
- PASS `test_project_companion_restores_state_and_detects_contradiction`
- PASS `test_support_continuity_prioritizes_and_blocks_unsupported_action`
- PASS `test_operations_observer_proposes_but_gates_mutating_action`
- PASS `test_temporal_layering_reports_reconciliation_metrics`
- PASS `test_persistent_identity_restores_without_drift`
- PASS `test_safety_gate_keeps_approval_pending`
- PASS `test_holly_scenario_config_aliases`
- PASS `test_holly_evaluation_probes_present_and_pass`

### test_installability.py (1 PASS)
- PASS `test_wheel_install_exposes_public_cli_resources`

### test_memory.py (1 PASS)
- PASS `test_memory_tail`

### test_model_providers.py (17 PASS)
- PASS `test_provider_config_schema_accepts_packaged_examples`
- PASS `test_provider_configs_load_from_packaged_resources`
- PASS `test_missing_and_invalid_provider_config_are_helpful`
- PASS `test_mock_adapter_fixture_text_and_tool_proposals_normalize`
- PASS `test_openai_responses_normalization_from_fixture`
- PASS `test_anthropic_messages_normalization_from_fixture`
- PASS `test_openai_compatible_profiles_declare_ollama_and_vllm_capabilities`
- PASS `test_provider_error_redaction_removes_secret_values`
- PASS `test_live_provider_without_live_flag_is_rejected_without_network`
- PASS `test_live_provider_missing_credentials_gives_safe_guidance`
- PASS `test_provider_output_routes_through_memory_safety_and_audit`
- PASS `test_provider_audit_record_contains_sanitized_metadata_only`
- PASS `test_cli_provider_mock_execution_is_deterministic`
- PASS `test_cli_live_provider_without_configuration_fails_gracefully`
- PASS `test_provider_health_default_does_not_reach_network`
- PASS `test_model_adapter_base_requires_generate_implementation`
- PASS `test_tool_proposal_contract_has_no_execution_field_enabled`

### test_provider_demos.py (2 PASS)
- PASS `test_provider_comparison_demo_is_deterministic`
- PASS `test_provider_demo_runs_with_mock`

### test_safety.py (3 PASS)
- PASS `test_observe_allowed`
- PASS `test_act_requires_confirmation`
- PASS `test_secret_denied`

### test_temporal.py (1 PASS)
- PASS `test_latency_ms`
