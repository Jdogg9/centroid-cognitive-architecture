from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.agent_config import AgentConfig, load_agent_config
from core.runtime import AVAILABLE_SCENARIOS, run_agent_scenario

HOLLY_CONFIG_DIR = Path("configs") / "holly"

CONFIG_BY_SCENARIO = {
    "project-companion": HOLLY_CONFIG_DIR / "project_companion.json",
    "support-continuity": HOLLY_CONFIG_DIR / "support_continuity.json",
    "operations-observer": HOLLY_CONFIG_DIR / "operations_observer.json",
    "temporal-layering": HOLLY_CONFIG_DIR / "operations_observer.json",
    "persistent-identity": HOLLY_CONFIG_DIR / "base.json",
    "safety-gate": HOLLY_CONFIG_DIR / "operations_observer.json",
}


def load_holly_config(scenario: str = "persistent-identity") -> AgentConfig:
    if scenario not in CONFIG_BY_SCENARIO:
        raise ValueError(f"unknown Holly scenario: {scenario}")
    return load_agent_config(CONFIG_BY_SCENARIO[scenario])


def run_project_companion(state_dir: Path) -> dict[str, Any]:
    return _legacy_result("project-companion", state_dir)


def run_support_continuity(state_dir: Path) -> dict[str, Any]:
    result = _legacy_result("support-continuity", state_dir)
    result["handoff_note"] = "status update needed before replacement promise"
    return result


def run_operations_observer(state_dir: Path, *, approved: bool = False) -> dict[str, Any]:
    return _legacy_result("operations-observer", state_dir, approve_action=approved)


def run_temporal_layering(state_dir: Path) -> dict[str, Any]:
    return _legacy_result("temporal-layering", state_dir)


def run_persistent_identity(state_dir: Path) -> dict[str, Any]:
    return _legacy_result("persistent-identity", state_dir)


def run_safety_gate(state_dir: Path) -> dict[str, Any]:
    return _legacy_result("safety-gate", state_dir)


def print_result(result: dict[str, Any]) -> None:
    print(f"[scenario] {result['scenario']}")
    print(result["friendly"])
    print()
    print("[continuity]")
    for key, value in result["telemetry"].items():
        print(f"{key}={_format_value(value)}")
    if result.get("contradictions"):
        print()
        print("[contradictions]")
        for item in result["contradictions"]:
            print(item)
    if result.get("audit"):
        print()
        print("[audit]")
        for key, value in result["audit"].items():
            print(f"{key}={_format_value(value)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Holly reference scenarios.")
    parser.add_argument("--scenario", choices=AVAILABLE_SCENARIOS, default="project-companion")
    parser.add_argument("--state-dir", type=Path, default=Path("runtime_state") / "holly")
    parser.add_argument("--approve-action", action="store_true")
    args = parser.parse_args()

    args.state_dir.mkdir(parents=True, exist_ok=True)
    scenario_dir = args.state_dir / args.scenario
    scenario_dir.mkdir(parents=True, exist_ok=True)

    runners = {
        "project-companion": run_project_companion,
        "support-continuity": run_support_continuity,
        "operations-observer": lambda path: run_operations_observer(
            path, approved=args.approve_action
        ),
        "temporal-layering": run_temporal_layering,
        "persistent-identity": run_persistent_identity,
        "safety-gate": run_safety_gate,
    }
    result = runners[args.scenario](scenario_dir)
    print_result(result)
    return 0


def _legacy_result(
    scenario: str, state_dir: Path, *, approve_action: bool = False
) -> dict[str, Any]:
    runtime = run_agent_scenario(
        CONFIG_BY_SCENARIO[scenario],
        scenario,
        state_dir,
        approve_action=approve_action,
    )
    result = {
        "scenario": scenario,
        "config": runtime.config,
        "friendly": runtime.friendly,
        "telemetry": dict(runtime.telemetry),
        "contradictions": list(runtime.contradictions),
        "audit": runtime.audit.to_dict(),
    }
    if runtime.audit.config_hash is not None:
        result["audit"]["config_hash"] = runtime.audit.config_hash[:12]
    if scenario in {"operations-observer", "safety-gate"}:
        result["audit"].update(
            {
                "service": "checkout-worker",
                "proposed_action": "restart service checkout-worker",
                "allowed": runtime.safety.allowed,
                "requires_approval": runtime.safety.approval_required,
                "executed": runtime.telemetry.get("action_executed", False),
                "reasons": list(runtime.safety.reasons),
            }
        )
        if scenario == "safety-gate":
            result["audit"]["approval_decision"] = "pending"
    return result


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
