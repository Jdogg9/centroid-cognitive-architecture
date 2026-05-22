from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

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
    args = parser.parse_args()

    args.state_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = args.state_dir / args.scenario
    scenario_dir.mkdir(parents=True, exist_ok=True)
    result = run_agent_scenario(
        args.config,
        args.scenario,
        scenario_dir,
        approve_action=args.approve_action,
    )
    print_result(result)
    return 0
