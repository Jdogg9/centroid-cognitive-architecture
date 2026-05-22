## Summary

Describe the change.

## Validation

- [ ] `python3 -B -m compileall core examples tests benchmarks configs evaluation schemas templates`
- [ ] `black --check --workers 1 core examples tests benchmarks configs evaluation schemas templates`
- [ ] `ruff check core examples tests benchmarks configs evaluation schemas templates`
- [ ] `pytest`
- [ ] `python3 -B examples/run_evaluation.py evaluation/fixtures/baseline.json`
- [ ] `python3 -B examples/run_demo.py --mode full`
- [ ] `python3 -B examples/run_temporal_demo.py`
- [ ] `python3 -B examples/run_identity_demo.py`
- [ ] all six `python3 -B examples/run_holly.py --scenario ...` demos
- [ ] `python3 -B benchmarks/run_all.py`
- [ ] `python3 -B -m build --wheel --no-isolation --outdir dist`
- [ ] clean wheel install smoke test for `centroid-holly`, `centroid-eval`, and `centroid-demo`

## Public Framing Check

- [ ] Does not introduce consciousness, sentience, phenomenology, personhood,
      subjective experience, or autonomous moral agency claims
- [ ] Uses neutral technical terminology
- [ ] Links new claims to tests, schemas, probes, or benchmarks
- [ ] Adds or updates evaluation fixtures for new measurable claims
- [ ] Adds or updates safety policy fixtures for safety-relevant behavior
- [ ] Updates documentation and limitations where behavior changes

## Safety Impact

Describe any effect on memory, routing, tool use, telemetry, safety gates,
shutdown compliance, or auditability.
