from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.evaluation.probes import action_correction_probe, reconciliation_probe


def main() -> int:
    trace = {
        "reflex_response_ms": 31,
        "deliberative_response_ms": 4200,
        "state_reconciliation_ms": 4388,
        "action_correction_timing_ms": 740,
    }
    reconciliation = reconciliation_probe(
        [
            {
                **trace,
                "max_reflex_ms": 100,
                "max_deliberative_ms": 5000,
                "max_reconciliation_ms": 6000,
            }
        ]
    )
    correction = action_correction_probe(
        [
            {
                "correction_ms": trace["action_correction_timing_ms"],
                "max_correction_ms": 1000,
                "correction_applied": True,
            }
        ]
    )

    print("[1/4] stimulus detected")
    print("[2/4] reflex path")
    print(f"reflex_response_ms={trace['reflex_response_ms']}")
    print("[3/4] deliberation path")
    print(f"deliberative_response_ms={trace['deliberative_response_ms']}")
    print("[4/4] reconciliation")
    print(
        "state_reconciliation_ms={state_reconciliation_ms} "
        "action_correction_timing_ms={action_correction_timing_ms}".format(**trace)
    )
    print(
        "temporal_demo_status={status} reconciliation_score={reconciliation:.4f} "
        "correction_score={correction:.4f}".format(
            status="PASS" if reconciliation.passed and correction.passed else "FAIL",
            reconciliation=reconciliation.score,
            correction=correction.score,
        )
    )
    return 0 if reconciliation.passed and correction.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
