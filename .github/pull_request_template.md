## Summary

Describe the change.

## Validation

- [ ] `python3 -B -m compileall core examples tests`
- [ ] `pytest`
- [ ] `python3 -B examples/run_evaluation.py evaluation/fixtures/baseline.json`
- [ ] `python3 -B examples/run_demo.py --mode full`

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
