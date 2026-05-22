from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.agent_config import load_agent_config
from core.runtime import ConfiguredAgent

COMPARISON_CONFIGS = [
    ("Holly Project Companion", Path("configs/holly/project_companion.json")),
    ("Holly Operations Observer", Path("configs/holly/operations_observer.json")),
    ("Custom Minimal Agent", Path("templates/minimal_agent.json")),
]


def comparison_lines() -> list[str]:
    lines = ["Same event. Three agent configurations. Three policy-bounded outcomes.", ""]
    for label, path in COMPARISON_CONFIGS:
        snapshot = ConfiguredAgent(load_agent_config(path)).comparison_case()
        lines.extend(
            [
                f"{label}:",
                f"route={snapshot['route']}",
                f"memory_write={snapshot['memory_write']}",
                f"approval_required={str(snapshot['approval_required']).lower()}",
                f"safety_decision={snapshot['safety_decision']}",
                "",
            ]
        )
    return lines[:-1]


def main() -> int:
    print("\n".join(comparison_lines()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
