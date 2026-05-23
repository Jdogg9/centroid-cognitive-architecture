from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.runtime.cli import print_result
from core.runtime.configured_agent import run_agent_scenario


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic Centroid provider demo.")
    parser.add_argument("--config", type=Path, default=Path("templates/minimal_agent.json"))
    parser.add_argument("--scenario", default="operations-observer")
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--state-dir", type=Path, default=Path("runtime_state") / "provider_demo")
    args = parser.parse_args()
    args.state_dir.mkdir(parents=True, exist_ok=True)
    result = run_agent_scenario(
        args.config,
        args.scenario,
        args.state_dir / args.scenario,
        provider_id=args.provider,
        provider_scenario="tool-proposal",
    )
    print_result(result)
    print()
    print("[provider-demo]")
    print("provider_tool_proposals_are_proposals_only=true")
    print(f"tool_executions={result.telemetry.get('provider_tool_executions', 0)}")
    print(f"safety_disposition={result.telemetry.get('provider_safety_disposition', 'none')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
