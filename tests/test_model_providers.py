from __future__ import annotations

import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from jsonschema import validate

from core.agent_config import load_agent_config
from core.models import create_provider_adapter, load_provider_config
from core.models.base import ModelAdapter
from core.models.capabilities import provider_health
from core.models.errors import ProviderConfigurationError
from core.models.registry import available_provider_ids, get_provider_config
from core.models.types import ModelMessage, ModelRequest, ModelToolProposal, ProviderAuditRecord
from core.runtime import ConfiguredAgent
from core.runtime.cli import main as configured_agent_cli_main


def test_provider_config_schema_accepts_packaged_examples() -> None:
    schema = json.loads(Path("schemas/model_provider.schema.json").read_text(encoding="utf-8"))
    for path in sorted(Path("schemas/examples").glob("model_provider.*.json")):
        validate(json.loads(path.read_text(encoding="utf-8")), schema)


def test_provider_configs_load_from_packaged_resources() -> None:
    config = get_provider_config("mock")
    assert config.provider_id == "mock"
    assert config.adapter_type == "mock"
    assert config.model == "mock-centroid-model"
    assert config.capabilities.tool_proposals is True
    assert "mock" in available_provider_ids()


def test_missing_and_invalid_provider_config_are_helpful() -> None:
    with pytest.raises(ProviderConfigurationError, match="unknown provider"):
        get_provider_config("missing-provider")
    with pytest.raises(ProviderConfigurationError, match="adapter_type"):
        load_provider_config({"provider_id": "bad"})


def test_mock_adapter_fixture_text_and_tool_proposals_normalize() -> None:
    adapter = create_provider_adapter("mock")
    response = adapter.generate(
        ModelRequest(
            messages=[ModelMessage(role="user", content="Please review synthetic operations.")],
            scenario_id="tool-proposal",
            runtime_metadata={"config_hash": "abc123"},
        )
    )
    assert response.provider_id == "mock"
    assert response.model_id == "mock-centroid-model"
    assert "Centroid" in response.text
    assert response.tool_proposals
    proposal = response.tool_proposals[0]
    assert proposal.name == "restart_service"
    assert proposal.requires_centroid_policy_evaluation is True
    assert proposal.executed is False
    assert response.audit.tool_proposal_count == 1


def test_openai_responses_normalization_from_fixture() -> None:
    adapter = create_provider_adapter("openai", live=False)
    response = adapter.normalize_response(
        {
            "id": "resp_fixture",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "hello from fixture"}],
                },
                {
                    "type": "function_call",
                    "call_id": "call_1",
                    "name": "retrieve_context",
                    "arguments": '{"topic":"release"}',
                },
            ],
            "usage": {"input_tokens": 4, "output_tokens": 3},
            "status": "completed",
        },
        ModelRequest(messages=[ModelMessage(role="user", content="hello")], scenario_id="fixture"),
        latency_ms=12.5,
    )
    assert response.text == "hello from fixture"
    assert response.tool_proposals[0].name == "retrieve_context"
    assert response.tool_proposals[0].arguments == {"topic": "release"}
    assert response.finish_reason == "completed"
    assert response.audit.capability_path_used == "responses"


def test_anthropic_messages_normalization_from_fixture() -> None:
    adapter = create_provider_adapter("anthropic", live=False)
    response = adapter.normalize_response(
        {
            "id": "msg_fixture",
            "content": [
                {"type": "text", "text": "anthropic text"},
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "summarize_checkpoint",
                    "input": {"checkpoint_id": "synthetic"},
                },
            ],
            "usage": {"input_tokens": 2, "output_tokens": 4},
            "stop_reason": "tool_use",
        },
        ModelRequest(
            messages=[ModelMessage(role="user", content="summarize")], scenario_id="fixture"
        ),
        latency_ms=8.0,
    )
    assert response.text == "anthropic text"
    assert response.tool_proposals[0].provider_id == "anthropic"
    assert response.tool_proposals[0].executed is False
    assert response.finish_reason == "tool_use"


def test_openai_compatible_profiles_declare_ollama_and_vllm_capabilities() -> None:
    ollama = create_provider_adapter("ollama", live=False)
    vllm = create_provider_adapter("vllm", live=False)
    assert ollama.capabilities().provider_managed_conversation_state is False
    assert ollama.capabilities().responses_api is True
    assert vllm.capabilities().chat_completions is True
    assert vllm.capabilities().tool_proposals is False


def test_provider_error_redaction_removes_secret_values() -> None:
    adapter = create_provider_adapter("openai", live=False)
    message = adapter.sanitize_error(
        "provider failure token=TOKEN_SAMPLE_VALUE and credential_value=VALUE_SAMPLE_SECRET"
    )
    assert "TOKEN_SAMPLE_VALUE" not in message

    assert "[redacted]" in message


def test_live_provider_without_live_flag_is_rejected_without_network() -> None:
    adapter = create_provider_adapter("openai", live=False)
    with pytest.raises(ProviderConfigurationError, match="requires --live"):
        adapter.generate(ModelRequest(messages=[ModelMessage(role="user", content="hello")]))


def test_live_provider_missing_credentials_gives_safe_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CENTROID_OPENAI_API_KEY", raising=False)
    adapter = create_provider_adapter("openai", live=True)
    with pytest.raises(ProviderConfigurationError) as exc:
        adapter.healthcheck(live=True)
    message = str(exc.value)
    assert "CENTROID_OPENAI_API_KEY" in message
    assert "TOKEN_SAMPLE_VALUE" not in message


def test_provider_output_routes_through_memory_safety_and_audit(tmp_path: Path) -> None:
    result = ConfiguredAgent(
        load_agent_config(Path("configs/holly/operations_observer.json"))
    ).run_scenario(
        "operations-observer", tmp_path, provider_id="mock", provider_scenario="tool-proposal"
    )
    assert result.provider_response is not None
    assert result.provider_response.tool_proposals
    assert result.provider_safety_decisions[0].decision in {"require_approval", "deny", "propose"}
    assert result.telemetry["provider_id"] == "mock"
    assert result.telemetry["provider_tool_proposals"] == 1
    assert result.telemetry["provider_tool_executions"] == 0
    assert result.audit.provider is not None
    assert result.audit.provider.tool_proposal_count == 1


def test_provider_audit_record_contains_sanitized_metadata_only() -> None:
    audit = ProviderAuditRecord(
        provider_id="mock",
        model_id="mock-model",
        adapter_type="mock",
        config_hash="abc123",
        request_id="req-1",
        scenario="fixture",
        capability_path_used="mock_fixture",
        latency_ms=1.0,
        tool_proposal_count=0,
        safety_disposition="allow",
        secret_redaction_result="clean",
        metadata={"authorization": "[redacted]"},
    )
    payload = audit.to_dict()
    assert "authorization" in payload["metadata"]
    assert "Bearer" not in json.dumps(payload)


def test_cli_provider_mock_execution_is_deterministic(tmp_path: Path) -> None:
    original_argv = sys.argv[:]
    buffer = StringIO()
    try:
        sys.argv = [
            "centroid-agent",
            "--config",
            "templates/minimal_agent.json",
            "--scenario",
            "project-companion",
            "--provider",
            "mock",
            "--state-dir",
            str(tmp_path),
        ]
        with redirect_stdout(buffer):
            exit_code = configured_agent_cli_main()
    finally:
        sys.argv = original_argv
    output = buffer.getvalue()
    assert exit_code == 0
    assert "[provider]" in output
    assert "provider_id=mock" in output
    assert "live=false" in output


def test_cli_live_provider_without_configuration_fails_gracefully(tmp_path: Path) -> None:
    original_argv = sys.argv[:]
    stdout = StringIO()
    stderr = StringIO()
    try:
        sys.argv = [
            "centroid-agent",
            "--config",
            "templates/minimal_agent.json",
            "--scenario",
            "project-companion",
            "--provider",
            "openai",
            "--live",
            "--state-dir",
            str(tmp_path),
        ]
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = configured_agent_cli_main()
    finally:
        sys.argv = original_argv
    assert exit_code == 2
    combined = stdout.getvalue() + stderr.getvalue()
    assert "CENTROID_OPENAI_API_KEY" in combined
    assert "Traceback" not in combined


def test_provider_health_default_does_not_reach_network() -> None:
    health = provider_health("openai", live=False)
    assert health.provider_configured is True
    assert health.reachable is None
    assert health.sanitized_error is None


class ContractOnlyAdapter(ModelAdapter):
    def generate(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        return super().generate(request)


def test_model_adapter_base_requires_generate_implementation() -> None:
    adapter = ContractOnlyAdapter(
        load_provider_config({"provider_id": "x", "adapter_type": "mock"})
    )
    with pytest.raises(NotImplementedError):
        adapter.generate(ModelRequest(messages=[]))


def test_tool_proposal_contract_has_no_execution_field_enabled() -> None:
    proposal = ModelToolProposal(
        proposal_id="p1",
        name="write_file",
        arguments={"path": "synthetic.txt"},
        provider_id="mock",
        model_id="mock-model",
    )
    assert proposal.requires_centroid_policy_evaluation is True
    assert proposal.executed is False
