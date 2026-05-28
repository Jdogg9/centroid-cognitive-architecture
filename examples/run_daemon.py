#!/usr/bin/env python3
"""Run the Centroid live daemon loop."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.daemon import CentroidDaemon, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Centroid live daemon loop")
    parser.add_argument("--config", default="config/daemon.yaml", help="path to daemon.yaml")
    parser.add_argument("--cycles", type=int, default=None, help="run N cycles then exit")
    parser.add_argument("--interval", type=float, default=None, help="override tick interval seconds")
    parser.add_argument("--dry-run", action="store_true", help="run 3 cycles, print CycleResults, exit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    if args.interval is not None:
        config.tick_interval_s = args.interval
    if args.cycles is not None:
        config.max_cycles = args.cycles

    daemon = CentroidDaemon.from_config(config)

    if args.dry_run:
        results = daemon.run_cycles(3)
        for result in results:
            print(
                f"cycle={result.cycle_number} "
                f"duration={result.duration_s:.3f}s "
                f"coherence={None if result.coherence_report is None else result.coherence_report.coherence_index} "
                f"anomalies={result.anomaly_count} "
                f"errors={len(result.errors)}"
            )
            if result.errors:
                for error in result.errors:
                    print(f"  error: {error}")
        return 1 if any(result.errors for result in results) else 0

    daemon.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
