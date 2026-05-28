"""Multi-horizon forecast generation using exponential smoothing.

Generates short (1 cycle), medium (5 cycle), and long (20 cycle)
forecasts from current metric values, with confidence calibrated
against historical accuracy.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from core.planner.calibration import CalibrationStore


HORIZONS: dict[str, int] = {
    "short": 1,
    "medium": 5,
    "long": 20,
}

DEFAULT_ALPHA = 0.3  # exponential smoothing weight


@dataclass
class Forecast:
    """A single horizon forecast for a set of metric fields."""

    horizon: Literal["short", "medium", "long"]
    cycle_distance: int                 # number of cycles ahead
    predictions: dict[str, float]       # {field: predicted_value}
    confidence: float                   # 0.0 – 1.0
    generated_at: float                 # time.time()
    forecast_id: str                    # uuid4 hex, for feedback linkage


class ForecastGenerator:
    """Generate multi-horizon forecasts with calibrated confidence."""

    def __init__(
        self,
        fields: list[str],
        *,
        alpha: float = DEFAULT_ALPHA,
    ) -> None:
        self._fields = list(fields)
        self._alpha = alpha
        # Per-field last prediction for smoothing
        self._last_predictions: dict[str, dict[str, float]] = {
            horizon: {f: 0.5 for f in fields}
            for horizon in HORIZONS
        }

    def generate(
        self,
        current_values: dict[str, float],
        calibration: CalibrationStore,
    ) -> list[Forecast]:
        """Generate one Forecast per horizon.

        Uses exponential smoothing:
            predicted = α × current + (1 − α) × last_predicted

        Confidence = 1.0 − mean(MAE across all fields for this horizon),
        using calibration history. Defaults to 0.5 if no history.
        """
        forecasts: list[Forecast] = []

        for horizon, cycle_distance in HORIZONS.items():
            predictions: dict[str, float] = {}
            maes: list[float] = []

            for field in self._fields:
                current = current_values.get(field, 0.5)
                last = self._last_predictions[horizon].get(field, 0.5)

                # Exponential smoothing
                predicted = self._alpha * current + (1.0 - self._alpha) * last
                predicted = round(predicted, 6)
                predictions[field] = predicted
                self._last_predictions[horizon][field] = predicted

                # Get historical MAE for this field+horizon
                rec = calibration.get(field, horizon)
                if rec is not None:
                    maes.append(rec.mae)

            # Confidence = 1.0 − mean MAE; 0.5 if no history
            if maes:
                confidence = 1.0 - sum(maes) / len(maes)
            else:
                confidence = 0.5
            confidence = round(max(0.0, min(1.0, confidence)), 6)

            forecasts.append(
                Forecast(
                    horizon=horizon,
                    cycle_distance=cycle_distance,
                    predictions=predictions,
                    confidence=confidence,
                    generated_at=time.time(),
                    forecast_id=uuid.uuid4().hex,
                )
            )

        return forecasts
