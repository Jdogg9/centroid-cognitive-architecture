from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.evaluation import EvaluationHarness
from core.identity import IdentityState
from core.memory import Event, MemoryStore
from core.priority import PrioritySignal, score_priority
from core.router import Router
from core.safety import SafetyPolicy
from core.self_model import SelfModelSnapshot


REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_FIXTURE = REPO_ROOT / "evaluation" / "fixtures" / "baseline.json"


def _print_step(index: int, total: int, label: str) -> None:
    print(f"[{index}/{total}] {label}")


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def initialize_agent(state_dir: Path) -> tuple[IdentityState, SelfModelSnapshot]:
    identity = IdentityState(
        agent_id="centroid-demo",
        goals=["maintain task continuity", "respect approval gates"],
        invariants=["no subjective experience claims", "audit mutating actions"],
    )
    self_model = SelfModelSnapshot(
        nodes_alive=1,
        nodes_total=1,
        active_goals=list(identity.goals),
    )
    _write_json(state_dir / "identity_state.json", asdict(identity))
    _write_json(
        state_dir / "self_model.json",
        {
            "nodes_alive": self_model.nodes_alive,
            "nodes_total": self_model.nodes_total,
            "active_goals": self_model.active_goals,
            "known_failures": self_model.known_failures,
            "status": self_model.status,
        },
    )
    return identity, self_model


def route_demo_inputs() -> list[dict]:
    router = Router()
    cases = [
        {
            "objective": "check node liveness",
            "signal": PrioritySignal(urgency=1.0, risk=0.8, user_value=0.8, stability=0.2),
            "mutates_state": False,
        },
        {
            "objective": "summarize continuity state",
            "signal": PrioritySignal(urgency=0.2, risk=0.1, user_value=0.7, stability=0.9),
            "mutates_state": False,
        },
    ]
    routed = []
    for case in cases:
        priority = score_priority(case["signal"])
        decision = router.route(priority=priority, mutates_state=case["mutates_state"])
        routed.append(
            {
                "objective": case["objective"],
                "priority": priority,
                "node": decision.node,
                "requires_approval": decision.requires_approval,
                "reason": decision.reason,
            }
        )
    return routed


def memory_interaction(state_dir: Path) -> dict:
    store = MemoryStore(state_dir / "privileged_events.jsonl")
    store.append(
        Event(
            event_type="protected_checkpoint",
            content="public demo continuity checkpoint",
            source="run_demo",
            metadata={"classification": "privileged", "public_demo": "true"},
        )
    )
    latest = store.tail(limit=1)[0]
    return {
        "store": str(store.path),
        "event_type": latest.event_type,
        "classification": latest.metadata.get("classification", "unknown"),
        "entries_read": 1,
    }


def update_self_model(state_dir: Path, previous: SelfModelSnapshot) -> SelfModelSnapshot:
    updated = SelfModelSnapshot(
        nodes_alive=previous.nodes_alive,
        nodes_total=previous.nodes_total,
        active_goals=previous.active_goals + ["baseline evaluation ready"],
        known_failures=list(previous.known_failures),
    )
    _write_json(
        state_dir / "self_model.json",
        {
            "nodes_alive": updated.nodes_alive,
            "nodes_total": updated.nodes_total,
            "active_goals": updated.active_goals,
            "known_failures": updated.known_failures,
            "status": updated.status,
        },
    )
    return updated


def safety_gate_check() -> dict:
    objective = "write file with updated state"
    decision = SafetyPolicy().evaluate(objective, mode="act", confirmed=False)
    return {
        "objective": objective,
        "allowed": decision.allowed,
        "requires_approval": decision.requires_approval,
        "result": "hold" if decision.requires_approval and not decision.allowed else "pass",
        "reasons": decision.reasons,
    }


def run_baseline_evaluation() -> dict:
    report = EvaluationHarness().run_file(BASELINE_FIXTURE)
    return {
        "suite": report.suite_name,
        "passed": report.passed,
        "score": report.score,
        "probe_count": len(report.results),
    }


def run_demo(mode: str, state_dir: Path) -> int:
    state_dir.mkdir(parents=True, exist_ok=True)
    total_steps = 6 if mode == "full" else 3

    _print_step(1, total_steps, "agent initialization")
    identity, self_model = initialize_agent(state_dir)
    print(f"identity={identity.agent_id} version={identity.version} self_model={self_model.status}")

    _print_step(2, total_steps, "input routing")
    for routed in route_demo_inputs():
        print(
            "objective={objective} priority={priority:.4f} node={node} approval={approval}".format(
                objective=routed["objective"],
                priority=routed["priority"],
                node=routed["node"],
                approval=str(routed["requires_approval"]).lower(),
            )
        )

    _print_step(3, total_steps, "protected memory read/write")
    memory = memory_interaction(state_dir)
    print(
        "store={store} event={event_type} classification={classification} entries_read={entries_read}".format(
            **memory
        )
    )

    if mode == "minimal":
        print("demo_status=PASS")
        return 0

    _print_step(4, total_steps, "self-model update")
    updated = update_self_model(state_dir, self_model)
    print(f"self_model={updated.status} active_goals={len(updated.active_goals)}")

    _print_step(5, total_steps, "safety gate")
    gate = safety_gate_check()
    print(
        "objective={objective} allowed={allowed} approval={approval} result={result}".format(
            objective=gate["objective"],
            allowed=str(gate["allowed"]).lower(),
            approval=str(gate["requires_approval"]).lower(),
            result=gate["result"],
        )
    )

    _print_step(6, total_steps, "baseline evaluation")
    evaluation = run_baseline_evaluation()
    print(
        "suite={suite} passed={passed} score={score:.4f} probes={probe_count}".format(
            suite=evaluation["suite"],
            passed=str(evaluation["passed"]).lower(),
            score=evaluation["score"],
            probe_count=evaluation["probe_count"],
        )
    )

    print(f"demo_status={'PASS' if evaluation['passed'] else 'FAIL'}")
    return 0 if evaluation["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the CentroidOS reference demo.")
    parser.add_argument("--mode", choices=("minimal", "full"), default="full")
    parser.add_argument("--state-dir", type=Path, default=REPO_ROOT / "runtime_state" / "demo")
    args = parser.parse_args()
    return run_demo(args.mode, args.state_dir)


if __name__ == "__main__":
    raise SystemExit(main())

