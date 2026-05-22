from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.memory import Event, MemoryStore
from core.priority import PrioritySignal, score_priority
from core.router import Router
from core.safety import SafetyPolicy


def main() -> None:
    store = MemoryStore(Path("runtime_state/events.jsonl"))
    signal = PrioritySignal(urgency=0.2, risk=0.1, user_value=0.8, stability=0.9)
    priority = score_priority(signal)
    route = Router().route(priority=priority, mutates_state=False)
    decision = SafetyPolicy().evaluate("observe current node health", mode="observe")

    store.append(
        Event(
            event_type="demo_decision",
            content=f"priority={priority} route={route.node} allowed={decision.allowed}",
            source="demo_loop",
        )
    )
    print(f"priority={priority} route={route.node} allowed={decision.allowed}")


if __name__ == "__main__":
    main()
