from examples.run_identity_demo import main as identity_demo_main
from examples.run_temporal_demo import main as temporal_demo_main


def test_additional_demos_pass() -> None:
    assert temporal_demo_main() == 0
    assert identity_demo_main() == 0
