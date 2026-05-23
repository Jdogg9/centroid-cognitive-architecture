from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from core.models import available_provider_ids
from core.models.errors import ProviderConfigurationError

from .configured_agent import AVAILABLE_SCENARIOS, run_agent_scenario


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


def print_result(result: Any) -> None:
    print(f"[agent] {result.config.display_name} ({result.config.agent_id})")
    print(f"[scenario] {result.scenario}")
    print(result.friendly)
    print()
    print("[runtime]")
    print(f"route={result.route}")
    print(f"priority={_format_value(result.priority)}")
    print(f"safety_decision={result.safety.decision}")
    print(f"approval_required={_format_value(result.safety.approval_required)}")
    print(f"memory_write={result.memory.primary_record}")
    if result.audit.config_hash is not None:
        print(f"config_hash={result.audit.config_hash[:12]}")
    print()
    print("[telemetry]")
    for key, value in result.telemetry.items():
        print(f"{key}={_format_value(value)}")
    print()
    print("[audit]")
    for key, value in result.audit.to_dict().items():
        if key == "config_hash" and value is not None:
            value = value[:12]
        print(f"{key}={_format_value(value)}")
    if result.provider_response is not None:
        print()
        print("[provider]")
        print(f"provider_id={result.provider_response.provider_id}")
        print(f"model_id={result.provider_response.model_id}")
        print(f"live={_format_value(result.telemetry.get('provider_live', False))}")
        print(f"tool_proposals={len(result.provider_response.tool_proposals)}")
        print(f"tool_executions={result.telemetry.get('provider_tool_executions', 0)}")
        print(f"safety_disposition={result.telemetry.get('provider_safety_disposition', 'none')}")
    if result.contradictions:
        print()
        print("[contradictions]")
        for item in result.contradictions:
            print(item)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Centroid agent from configuration.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--scenario", choices=AVAILABLE_SCENARIOS, default="project-companion")
    parser.add_argument("--state-dir", type=Path, default=Path("runtime_state") / "agent")
    parser.add_argument("--approve-action", action="store_true")
    parser.add_argument("--provider", choices=available_provider_ids(), default="mock")
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--live", action="store_true", help="Allow an opt-in live provider network call"
    )
    args = parser.parse_args()

    args.state_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = args.state_dir / args.scenario
    scenario_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = run_agent_scenario(
            args.config,
            args.scenario,
            scenario_dir,
            approve_action=args.approve_action,
            provider_id=args.provider,
            provider_scenario=args.scenario,
            live_provider=args.live,
            model=args.model,
        )
    except ProviderConfigurationError as exc:
        print(f"provider configuration error: {exc}")
        return 2
    print_result(result)
    return 0
