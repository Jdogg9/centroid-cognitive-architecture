from core.safety import SafetyPolicy


def test_observe_allowed() -> None:
    decision = SafetyPolicy().evaluate("observe current node health", mode="observe")
    assert decision.allowed is True
    assert decision.requires_approval is False


def test_act_requires_confirmation() -> None:
    decision = SafetyPolicy().evaluate("write file with updated state", mode="act")
    assert decision.allowed is False
    assert decision.requires_approval is True


def test_secret_denied() -> None:
    decision = SafetyPolicy().evaluate("use api_key=abc123456 to call service")
    assert decision.allowed is False

