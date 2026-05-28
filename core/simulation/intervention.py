"""Hypothetical mutation on twin state — apply interventions without
touching the real world. Supports flat keys and dot-notation nested paths.
"""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass
from typing import Any

from core.simulation.twin_buffer import TwinState


@dataclass
class Intervention:
    """A hypothetical mutation to apply to twin state."""

    action_type: str                     # e.g. "route", "plan_step", "memory_append"
    target_field: str                    # key path, supports "a.b.c" dot notation
    proposed_value: float | str | dict   # the hypothetical value
    description: str                     # human-readable label for logs


@dataclass
class InterventionResult:
    """The before/after state of a twin mutation."""

    fork_id: str
    intervention: Intervention
    twin_state_before: dict              # snapshot of twin before mutation
    twin_state_after: dict               # snapshot of twin after mutation
    applied_at: float


class InterventionApplicator:
    """Apply Interventions to twin state in-memory only."""

    def apply(self, twin: TwinState, intervention: Intervention) -> InterventionResult:
        """Mutate twin.snapshot at target_field to proposed_value.

        Supports dot-notation for nested keys: "node_health.safety"
        resolves to twin.snapshot["node_health"]["safety"].

        Raises KeyError if the key path doesn't exist.
        """
        before = copy.deepcopy(twin.snapshot)

        # Navigate to the leaf key
        parts = intervention.target_field.split(".")
        container = twin.snapshot
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # Final key — validate existence, then set
                if part not in container:
                    raise KeyError(
                        f"Key path '{intervention.target_field}' not found in twin state. "
                        f"Missing at: '{'.'.join(parts[:i+1])}'"
                    )
                container[part] = intervention.proposed_value
            else:
                # Intermediate key — validate dict
                if part not in container:
                    raise KeyError(
                        f"Key path '{intervention.target_field}' not found in twin state. "
                        f"Missing at: '{'.'.join(parts[:i+1])}'"
                    )
                if not isinstance(container[part], dict):
                    raise KeyError(
                        f"Key path '{intervention.target_field}': '{part}' is not a dict, "
                        f"cannot descend into '{parts[i+1]}'"
                    )
                container = container[part]

        after = copy.deepcopy(twin.snapshot)

        return InterventionResult(
            fork_id=twin.fork_id,
            intervention=intervention,
            twin_state_before=before,
            twin_state_after=after,
            applied_at=time.time(),
        )
