from pathlib import Path

from core.self_model import SelfModelSnapshot


def test_self_model_status_classification() -> None:
    assert SelfModelSnapshot(nodes_alive=3, nodes_total=3).status == "healthy"
    assert SelfModelSnapshot(nodes_alive=1, nodes_total=3).status == "degraded"
    assert SelfModelSnapshot(nodes_alive=0, nodes_total=3).status == "critical"


def test_non_claims_are_explicit() -> None:
    text = Path("docs/NON_CLAIMS.md").read_text(encoding="utf-8").lower()
    required = [
        "machine consciousness",
        "sentience",
        "subjective phenomenology",
        "autonomous personhood",
        "subjective experience",
        "autonomous moral agency",
    ]
    for phrase in required:
        assert phrase in text
