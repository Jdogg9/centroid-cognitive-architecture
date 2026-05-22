from datetime import datetime, timedelta

from core.temporal import latency_ms


def test_latency_ms() -> None:
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(seconds=1.25)
    assert latency_ms(start, end) == 1250.0
