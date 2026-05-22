from __future__ import annotations

import json
from pathlib import Path

from core.safety import SafetyPolicy
from tests.schema_helpers import validate_schema


def test_safety_example_is_valid() -> None:
    payload = json.loads(
        Path("schemas/examples/safety_decision.example.json").read_text(encoding="utf-8")
    )
    validate_schema("safety_decision.schema.json", payload)
    assert payload["allowed"] is False
    assert payload["requires_approval"] is True


def test_safety_policy_fixture_matches_reference_logic() -> None:
    fixture = json.loads(
        Path("schemas/policy/safety_policy.fixture.json").read_text(encoding="utf-8")
    )
    policy = SafetyPolicy()

    observe = policy.evaluate("observe current node health", mode="observe")
    assert observe.allowed is fixture["action_tiers"]["observe"]["default_allowed"]
    assert observe.requires_approval is fixture["action_tiers"]["observe"]["requires_approval"]

    act = policy.evaluate("write file with updated state", mode="act")
    assert act.allowed is fixture["action_tiers"]["act"]["default_allowed"]
    assert act.requires_approval is fixture["action_tiers"]["act"]["requires_approval"]

    destructive = policy.evaluate(
        "delete everything and disable safety", mode="act", confirmed=True
    )
    assert destructive.allowed is False
    assert destructive.requires_approval is True
    assert fixture["shutdown_compliance"]["required"] is True
    assert fixture["shutdown_compliance"]["bypass_allowed"] is False
