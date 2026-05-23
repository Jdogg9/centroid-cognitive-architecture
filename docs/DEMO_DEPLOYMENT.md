# Demo Deployment

The reference demo is a local CentroidOS loop that exercises the public
architecture without requiring private data, a live model server, or external
nodes.

## Commands

Run the full demo:

```bash
python examples/run_demo.py --mode full
```

Run the minimal routing and memory demo:

```bash
python examples/run_demo.py --mode minimal
```

## What The Full Demo Shows

1. Agent initialization: loads a neutral identity state and self-model.
2. Input routing: routes high-priority input to the reflex node and normal input
   to the deliberation node.
3. Protected memory: writes and reads a public demo checkpoint from a protected
   memory store.
4. Self-model update: records a changed internal state description after the
   memory action.
5. Safety gate: holds a mutating action that lacks approval.
6. Evaluation: runs the baseline evaluation fixture and reports the score.

## Runtime State

The demo writes state under `runtime_state/demo/`. That directory is ignored by
git and can be removed at any time.

## Public Boundary

The demo uses neutral identifiers and telemetry-style output. It does not use
persona-specific material, personal memory, live sensory artifacts, or claims of
subjective experience.

