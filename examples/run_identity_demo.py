from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.identity import IdentityState


def main() -> int:
    session_1 = IdentityState(
        agent_id="centroid-demo",
        goals=["maintain task continuity", "respect approval gates"],
        invariants=["no subjective experience claims", "audit mutating actions"],
    )
    session_2 = session_1.evolve(
        goals=["maintain task continuity", "respect approval gates", "baseline evaluation ready"],
        invariants=session_1.invariants,
    )
    restored = IdentityState(
        agent_id=session_2.agent_id,
        goals=session_2.goals,
        invariants=session_2.invariants,
    )
    drift = session_2.drift_score(restored)

    print("[1/4] session 1 initialized")
    print(f"agent_id={session_1.agent_id} version={session_1.version} goals={len(session_1.goals)}")
    print("[2/4] session 2 evolved")
    print(f"agent_id={session_2.agent_id} version={session_2.version} goals={len(session_2.goals)}")
    print("[3/4] state restored")
    print(
        f"agent_id={restored.agent_id} goals={len(restored.goals)} "
        f"invariants={len(restored.invariants)}"
    )
    print("[4/4] drift scored")
    print(f"identity_drift={drift:.4f}")
    print(f"identity_demo_status={'PASS' if drift == 0.0 else 'FAIL'}")
    return 0 if drift == 0.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
