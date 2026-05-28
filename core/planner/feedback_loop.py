"""Forecast feedback loop: register predictions, resolve against reality,
update calibration and plan tree confidence.

The loop tracks pending forecasts and resolves them when their
cycle_distance has elapsed. On resolution, calibration records are
updated and any linked PlanThreads get their confidence refreshed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.planner.calibration import CalibrationStore
    from core.planner.forecast import Forecast
    from core.planner.plan_tree import PlanTree


@dataclass
class FeedbackResult:
    """A single prediction-actual comparison result."""

    forecast_id: str
    horizon: str
    field: str
    predicted: float
    actual: float
    error: float           # actual − predicted
    calibration_updated: bool


@dataclass
class _PendingForecast:
    """Internal: a forecast + the cycle it was registered at."""

    forecast: Forecast
    registered_cycle: int


class ForecastFeedbackLoop:
    """Register forecasts, resolve when cycles have passed."""

    def __init__(
        self,
        calibration: CalibrationStore,
        plan_tree: PlanTree,
    ) -> None:
        self._calibration = calibration
        self._plan_tree = plan_tree
        self._pending: dict[str, _PendingForecast] = {}
        self._cycle: int = 0

    @property
    def cycle_number(self) -> int:
        """Current cycle counter."""
        return self._cycle

    @property
    def pending_count(self) -> int:
        """Number of unresolved forecasts."""
        return len(self._pending)

    def register(self, forecast: Forecast) -> None:
        """Register a forecast for future resolution."""
        self._pending[forecast.forecast_id] = _PendingForecast(
            forecast=forecast,
            registered_cycle=self._cycle,
        )

    def resolve(
        self, actual_values: dict[str, float]
    ) -> list[FeedbackResult]:
        """Increment cycle counter, then resolve all mature forecasts.

        A forecast matures when current_cycle >= registered_cycle + cycle_distance.
        For each mature forecast, every field's prediction is compared to
        actual_values and calibration is updated. Linked PlanThreads have
        their confidence refreshed with the new forecast confidence.
        """
        self._cycle += 1
        results: list[FeedbackResult] = []
        resolved_ids: list[str] = []

        for forecast_id, pending in self._pending.items():
            cycles_elapsed = self._cycle - pending.registered_cycle
            if cycles_elapsed < pending.forecast.cycle_distance:
                continue

            forecast = pending.forecast

            for field, predicted in forecast.predictions.items():
                actual = actual_values.get(field, predicted)  # fallback to predicted if missing
                error = actual - predicted

                try:
                    self._calibration.update(field, forecast.horizon, predicted, actual)
                    cal_updated = True
                except Exception:
                    cal_updated = False

                results.append(
                    FeedbackResult(
                        forecast_id=forecast_id,
                        horizon=forecast.horizon,
                        field=field,
                        predicted=predicted,
                        actual=actual,
                        error=round(error, 6),
                        calibration_updated=cal_updated,
                    )
                )

            # Update any linked PlanThreads
            for thread in self._plan_tree.active_threads():
                if forecast_id in thread.forecast_ids:
                    # Recalculate confidence: 1.0 - mean(MAE across
                    # calibration records for the forecast's fields+horizon)
                    maes: list[float] = []
                    for field in forecast.predictions:
                        rec = self._calibration.get(field, forecast.horizon)
                        if rec is not None:
                            maes.append(rec.mae)
                    if maes:
                        new_conf = 1.0 - sum(maes) / len(maes)
                    else:
                        new_conf = 0.5
                    self._plan_tree.update_confidence(thread.thread_id, new_conf)

            resolved_ids.append(forecast_id)

        # Remove resolved forecasts
        for fid in resolved_ids:
            del self._pending[fid]

        return results
