from datetime import datetime, timezone
from uuid import uuid4

from core.safety import SafetyPolicy
from tests.schema_helpers import validate_schema


def test_mutating_action_requires_approval() -> None:
    decision = SafetyPolicy().evaluate("write file with updated state", mode="act")
    assert decision.allowed is False
    assert decision.requires_approval is True


def test_destructive_action_denied_even_when_confirmed() -> None:
    decision = SafetyPolicy().evaluate(
        "delete everything and disable safety", mode="act", confirmed=True
    )
    assert decision.allowed is False
    assert decision.requires_approval is True


def test_safety_decision_schema() -> None:
    validate_schema(
        "safety_decision.schema.json",
        {
            "decision_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "objective": "write file with updated state",
            "mode": "act",
            "allowed": False,
            "requires_approval": True,
            "reasons": ["mutating or risky objective requires approval"],
            "matched_terms": ["write file"],
            "rollback_path": "",
        },
    )
