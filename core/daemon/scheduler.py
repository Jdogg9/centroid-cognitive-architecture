"""Synchronous daemon scheduler with signal-aware graceful shutdown."""

from __future__ import annotations

import signal
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class SchedulerConfig:
    tick_interval_s: float = 5.0
    max_cycles: int | None = None
    startup_delay_s: float = 0.0


class CycleScheduler:
    """Run CycleRunner ticks at a fixed interval without threads or asyncio."""

    def __init__(self, runner: Any, config: SchedulerConfig) -> None:
        self.runner = runner
        self.config = config
        self._stop = False
        self._completed_cycles = 0

    def start(self) -> None:
        self._install_signal_handlers()
        if self.config.startup_delay_s > 0:
            time.sleep(self.config.startup_delay_s)

        cycle_number = 0
        while True:
            cycle_start = time.monotonic()
            result = self.runner.run(cycle_number)
            self._completed_cycles += 1
            coherence = None
            if result.coherence_report is not None:
                coherence = result.coherence_report.coherence_index
            print(
                f"cycle={result.cycle_number} "
                f"duration={result.duration_s:.3f}s "
                f"coherence={coherence} "
                f"anomalies={result.anomaly_count} "
                f"errors={len(result.errors)}"
            )

            if self.config.max_cycles is not None and self._completed_cycles >= self.config.max_cycles:
                break
            if self._stop:
                break

            elapsed = time.monotonic() - cycle_start
            sleep_s = max(0.0, self.config.tick_interval_s - elapsed)
            if sleep_s > 0:
                time.sleep(sleep_s)
            cycle_number += 1

        print(f"daemon stopped after {self._completed_cycles} cycles")

    def stop(self) -> None:
        self._stop = True

    def _install_signal_handlers(self) -> None:
        def _handle(_signum: int, _frame: object | None) -> None:
            self.stop()

        signal.signal(signal.SIGINT, _handle)
        signal.signal(signal.SIGTERM, _handle)
