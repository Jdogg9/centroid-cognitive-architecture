# Contributing

Centroid welcomes contributions that improve reproducibility, safety,
documentation quality, evaluation coverage, and architectural clarity.

## Contribution Priorities

- deterministic tests and evaluation fixtures
- benchmark suites for latency, memory consistency, and distributed coordination
- clearer documentation and diagrams
- safety policy improvements
- neutral terminology that avoids consciousness or personhood claims
- small, well-scoped reference implementations

## Public Language Rules

Use neutral technical terminology:

- distributed persistent cognitive architecture
- recursive self-modeling
- temporal stratification
- persistent identity continuity
- priority-weighted regulation
- distributed coordination

Do not introduce claims of consciousness, sentience, subjective experience,
phenomenology, autonomous personhood, or autonomous moral agency.

## Development Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
python examples/run_evaluation.py evaluation/fixtures/baseline.json
python examples/run_demo.py --mode full
```

## Pull Request Expectations

- Explain what changed and why.
- Link claims to tests, probes, benchmarks, or docs.
- Keep private-origin framing out of public examples.
- Add or update evaluation fixtures for new measurable claims.
- Preserve the non-claims boundary.

## Safety Expectations

Changes that affect action execution, persistence, routing, telemetry, or memory
must describe their safety impact. Mutating behavior should be approval-gated,
auditable, and reversible where practical.

