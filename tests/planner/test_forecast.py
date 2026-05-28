"""Probe tests for multi-horizon forecasting, calibration, plan trees,
and the feedback loop that closes the predict→resolve→calibrate cycle.

All probes must pass at score=1.0.
"""

from __future__ import annotations

import time

import pytest

from core.planner import (
    CalibrationStore,
    ForecastFeedbackLoop,
    ForecastGenerator,
    Plan,
    PlanStep,
    PlanTree,
)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _tmp_cal(tmp_path, suffix: str = "") -> CalibrationStore:
    return CalibrationStore(state_path=str(tmp_path / "state" / f"calibration{suffix}.json"))


def _tmp_pt(tmp_path, suffix: str = "", **kwargs) -> PlanTree:
    return PlanTree(
        state_path=str(tmp_path / "state" / f"plan_tree{suffix}.json"),
        **kwargs,
    )


# ── Planner backward compatibility ────────────────────────────────────────


def test_plan_step_backward_compat() -> None:
    """PlanStep and Plan still import and work identically."""
    step = PlanStep("test action", mutates_state=True, requires_approval=True)
    assert step.description == "test action"
    assert step.mutates_state is True

    plan = Plan("test objective", steps=[step])
    assert plan.requires_approval() is True


# ── Forecast generation ──────────────────────────────────────────────────


def test_forecast_generates_three_horizons(tmp_path) -> None:
    """generate() returns short, medium, and long forecasts."""
    cal = _tmp_cal(tmp_path, "_f1")
    fg = ForecastGenerator(fields=["memory", "router"])
    forecasts = fg.generate({"memory": 0.9, "router": 0.7}, cal)
    assert len(forecasts) == 3
    horizons = {f.horizon for f in forecasts}
    assert horizons == {"short", "medium", "long"}


def test_forecast_confidence_cold_start(tmp_path) -> None:
    """confidence = 0.5 with no calibration history."""
    cal = _tmp_cal(tmp_path, "_f2")
    fg = ForecastGenerator(fields=["cpu"])
    forecasts = fg.generate({"cpu": 0.8}, cal)
    for f in forecasts:
        assert f.confidence == 0.5


def test_forecast_id_unique(tmp_path) -> None:
    """Each generate() call produces unique forecast_ids."""
    cal = _tmp_cal(tmp_path, "_f3")
    fg = ForecastGenerator(fields=["x"])
    ids = set()
    for _ in range(5):
        forecasts = fg.generate({"x": 0.5}, cal)
        for f in forecasts:
            ids.add(f.forecast_id)
    assert len(ids) == 15  # 5 calls × 3 horizons = 15 unique IDs


def test_forecast_predictions_approach_current_over_time(tmp_path) -> None:
    """Multiple generate() calls with same current value converge via smoothing."""
    cal = _tmp_cal(tmp_path, "_f4")
    fg = ForecastGenerator(fields=["mem"], alpha=0.5)

    # First call: last=0.5, current=0.9 → pred = 0.5×0.9 + 0.5×0.5 = 0.7
    f1 = fg.generate({"mem": 0.9}, cal)
    assert f1[0].predictions["mem"] == pytest.approx(0.7, abs=0.01)

    # Second call: last=0.7, current=0.9 → pred = 0.5×0.9 + 0.5×0.7 = 0.8
    f2 = fg.generate({"mem": 0.9}, cal)
    assert f2[0].predictions["mem"] == pytest.approx(0.8, abs=0.01)


# ── Calibration ──────────────────────────────────────────────────────────


def test_calibration_update_incremental(tmp_path) -> None:
    """MAE decreases on perfect predictions."""
    cal = _tmp_cal(tmp_path, "_c1")
    # Add some error first
    cal.update("cpu", "short", 0.8, 0.6)  # error=0.2, mae=0.2
    r1 = cal.get("cpu", "short")
    assert r1 is not None
    assert r1.mae == 0.2
    assert r1.sample_count == 1

    # Perfect prediction improves MAE
    cal.update("cpu", "short", 0.5, 0.5)  # error=0.0
    r2 = cal.get("cpu", "short")
    assert r2 is not None
    assert r2.mae < 0.2  # (0.2×1 + 0.0) / 2 = 0.1
    assert r2.sample_count == 2


def test_calibration_bias_signed(tmp_path) -> None:
    """over-predict → positive bias, under-predict → negative bias."""
    cal = _tmp_cal(tmp_path, "_c2")
    cal.update("cpu", "medium", 0.9, 0.5)  # predicted > actual → positive bias
    r = cal.get("cpu", "medium")
    assert r is not None
    assert r.bias > 0.0

    cal2 = _tmp_cal(tmp_path, "_c3")
    cal2.update("cpu", "medium", 0.1, 0.5)  # predicted < actual → negative bias
    r2 = cal2.get("cpu", "medium")
    assert r2 is not None
    assert r2.bias < 0.0


def test_calibration_persists_to_disk(tmp_path) -> None:
    """state/calibration.json is written after update."""
    cal = CalibrationStore(state_path=str(tmp_path / "state" / "calibration.json"))
    cal.update("field", "short", 0.5, 0.5)
    # File should exist
    p = tmp_path / "state" / "calibration.json"
    assert p.exists()


def test_calibration_load_roundtrip(tmp_path) -> None:
    """A new CalibrationStore reads back the records written by a previous one."""
    path = str(tmp_path / "cal.json")
    cal1 = CalibrationStore(state_path=path)
    cal1.update("cpu", "short", 0.8, 0.6)

    cal2 = CalibrationStore(state_path=path)
    r = cal2.get("cpu", "short")
    assert r is not None
    assert r.mae == 0.2  # same as cal1 recorded
    assert r.sample_count == 1


def test_calibration_all_records(tmp_path) -> None:
    """all_records() returns all tracked pairs."""
    cal = _tmp_cal(tmp_path, "_ar")
    cal.update("a", "short", 0.5, 0.5)
    cal.update("b", "medium", 0.5, 0.5)
    records = cal.all_records()
    assert len(records) == 2
    fields = {r.field for r in records}
    horizons = {r.horizon for r in records}
    assert "a" in fields and "b" in fields
    assert "short" in horizons and "medium" in horizons


# ── Plan tree ────────────────────────────────────────────────────────────


def test_plan_tree_add_active(tmp_path) -> None:
    """New thread starts as active."""
    pt = _tmp_pt(tmp_path, "_1")
    t = pt.add_thread("test goal", [PlanStep("step1")], 0.8)
    assert t.status == "active"
    assert t.goal == "test goal"
    assert len(pt.active_threads()) == 1


def test_plan_tree_abandon_threshold(tmp_path) -> None:
    """Confidence below threshold → status=abandoned."""
    pt = _tmp_pt(tmp_path, "_2", abandon_threshold=0.3)
    t = pt.add_thread("goal", [PlanStep("s")], 0.5)
    pt.update_confidence(t.thread_id, 0.2)  # below 0.3
    assert t.status == "abandoned"
    assert len(pt.active_threads()) == 0


def test_plan_tree_complete(tmp_path) -> None:
    """complete() sets status=completed."""
    pt = _tmp_pt(tmp_path, "_3")
    t = pt.add_thread("goal", [PlanStep("s")], 0.8)
    pt.complete(t.thread_id)
    assert t.status == "completed"
    assert len(pt.active_threads()) == 0


def test_plan_tree_active_filter(tmp_path) -> None:
    """active_threads() excludes abandoned and completed."""
    pt = _tmp_pt(tmp_path, "_4")
    t1 = pt.add_thread("active", [PlanStep("s")], 0.8)
    t2 = pt.add_thread("abandoned", [PlanStep("s")], 0.5)
    t3 = pt.add_thread("completed", [PlanStep("s")], 0.8)

    pt.update_confidence(t2.thread_id, 0.1)
    pt.complete(t3.thread_id)

    active = pt.active_threads()
    assert len(active) == 1
    assert active[0].thread_id == t1.thread_id


def test_plan_tree_all_threads(tmp_path) -> None:
    """all_threads() returns all regardless of status."""
    pt = _tmp_pt(tmp_path, "_5")
    pt.add_thread("a", [PlanStep("s")], 0.8)
    pt.add_thread("b", [PlanStep("s")], 0.8)
    assert len(pt.all_threads()) == 2


# ── Feedback loop ────────────────────────────────────────────────────────


def test_feedback_loop_register_resolve(tmp_path) -> None:
    """Short-horizon forecast resolves after 1 cycle."""
    cal = _tmp_cal(tmp_path, "_fl1")
    pt = _tmp_pt(tmp_path, "_fl_pt1")
    fl = ForecastFeedbackLoop(cal, pt)

    fg = ForecastGenerator(fields=["cpu"])
    forecasts = fg.generate({"cpu": 0.8}, cal)
    short_forecast = [f for f in forecasts if f.horizon == "short"][0]

    fl.register(short_forecast)
    assert fl.pending_count == 1

    # Resolve at cycle 1: short (1 cycle) matures
    predicted = short_forecast.predictions["cpu"]
    actual = 0.75
    results = fl.resolve({"cpu": actual})
    assert len(results) == 1
    assert results[0].forecast_id == short_forecast.forecast_id
    assert results[0].field == "cpu"
    expected_error = actual - predicted
    assert results[0].error == pytest.approx(expected_error, abs=0.01)
    assert fl.pending_count == 0


def test_feedback_loop_calibration_updated(tmp_path) -> None:
    """resolve() updates calibration records."""
    cal = _tmp_cal(tmp_path, "_fl2")
    pt = _tmp_pt(tmp_path, "_fl_pt2")
    fl = ForecastFeedbackLoop(cal, pt)

    fg = ForecastGenerator(fields=["cpu"])
    forecasts = fg.generate({"cpu": 0.8}, cal)
    fl.register(forecasts[0])  # short horizon

    assert cal.get("cpu", "short") is None  # no record yet
    results = fl.resolve({"cpu": 0.75})
    r = cal.get("cpu", "short")
    assert r is not None
    assert r.sample_count == 1
    # FeedbackResult carries the calibration_updated flag
    assert results[0].calibration_updated is True


def test_feedback_loop_medium_delayed(tmp_path) -> None:
    """Medium-horizon forecast does NOT resolve until cycle 5."""
    cal = _tmp_cal(tmp_path, "_fl3")
    pt = _tmp_pt(tmp_path, "_fl_pt3")
    fl = ForecastFeedbackLoop(cal, pt)

    fg = ForecastGenerator(fields=["cpu"])
    forecasts = fg.generate({"cpu": 0.8}, cal)
    medium = [f for f in forecasts if f.horizon == "medium"][0]
    fl.register(medium)

    # Cycle 1: medium should not resolve yet (needs 5 cycles)
    results1 = fl.resolve({"cpu": 0.75})
    assert fl.pending_count == 1  # still pending
    assert len([r for r in results1 if r.horizon == "medium"]) == 0

    # Cycles 2-4: still not mature
    for _ in range(3):
        fl.resolve({"cpu": 0.75})
    assert fl.pending_count == 1

    # Cycle 5: now mature
    results5 = fl.resolve({"cpu": 0.75})
    assert len([r for r in results5 if r.horizon == "medium"]) == 1
    assert fl.pending_count == 0


def test_feedback_loop_confidence_update(tmp_path) -> None:
    """Linked PlanThread confidence updated on forecast resolution."""
    cal = _tmp_cal(tmp_path, "_fl4")
    pt = _tmp_pt(tmp_path, "_fl_pt4", abandon_threshold=0.1)
    fl = ForecastFeedbackLoop(cal, pt)

    fg = ForecastGenerator(fields=["cpu"])
    forecasts = fg.generate({"cpu": 0.8}, cal)
    short = forecasts[0]

    # Thread linked to this forecast
    t = pt.add_thread(
        "linked goal",
        [PlanStep("step")],
        initial_confidence=0.5,
        forecast_ids=[short.forecast_id],
    )
    assert t.confidence == 0.5

    fl.register(short)
    # Feed actual ≈ predicted so MAE stays low → high confidence
    predicted = short.predictions["cpu"]
    fl.resolve({"cpu": predicted})

    # After resolution, thread confidence should have been recalculated
    updated = pt.get(t.thread_id)
    assert updated is not None
    assert updated.confidence > 0.5  # improved from calibration
