"""Safety preflight: run counterfactual twin simulation before committing
to mutating actions. If divergence from actual state exceeds threshold,
escalate the safety decision.

Integrates with the existing safety policy tier system:
  allow → may escalate to hold
  hold  → passes through unchanged
  deny  → passes through unchanged (never downgraded)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from core.simulation.divergence import DivergenceCalculator
from core.simulation.intervention import Intervention, InterventionApplicator
from core.simulation.twin_buffer import TwinBuffer

if TYPE_CHECKING:
    from core.coherence.coherence_graph import CoherenceGraph
    from core.coherence.do_operator import DoIntervention


@dataclass
class PreflightVerdict:
    """The result of a twin-simulation safety preflight."""

    fork_id: str
    action_type: str
    divergence: float
    threshold: float
    escalated: bool                      # True if divergence > threshold
    original_decision: str               # "allow" / "hold" / "deny"
    final_decision: str                  # may upgrade "allow" → "hold"
    reason: str


class SafetyPreflight:
    """Run twin-world simulations before committing to mutating actions.

    Read-only with respect to the real world: never writes to
    world_snapshot.json, never calls memory_store.append().
    The caller decides whether to log the verdict.
    """

    def __init__(
        self,
        twin_buffer: TwinBuffer,
        applicator: InterventionApplicator,
        calculator: DivergenceCalculator,
        coherence_graph: CoherenceGraph | None = None,
        divergence_threshold: float = 0.25,
        simulation_cycles: int = 3,
    ) -> None:
        self._twin_buffer = twin_buffer
        self._applicator = applicator
        self._calculator = calculator
        self._coherence_graph = coherence_graph
        self._threshold = divergence_threshold
        self._simulation_cycles = simulation_cycles

    def evaluate(
        self,
        intervention: Intervention,
        original_decision: str,
    ) -> PreflightVerdict:
        """Run a full twin-simulation preflight.

        1. Fork current state
        2. Apply the intervention to the twin
        3. Propagate through coherence graph (if configured)
        4. Sample divergence over simulation_cycles
        5. Compute weighted divergence metric
        6. Escalate if divergence exceeds threshold

        `original_decision` should be one of "allow", "hold", or "deny"
        (from the existing safety policy).
        """
        # 1. Fork
        twin = self._twin_buffer.fork()

        # 2. Apply intervention (mutates twin.snapshot in-place)
        self._applicator.apply(twin, intervention)

        # 3. Propagate through coherence graph
        if self._coherence_graph is not None:
            from core.coherence.do_operator import DoIntervention

            # Try to map target_field to a coherence graph node
            # Use the top-level key (before first dot) as the node_id candidate
            top_key = intervention.target_field.split(".")[0]
            do_int = DoIntervention(node_id=top_key, fixed_value=float(intervention.proposed_value) if isinstance(intervention.proposed_value, (int, float)) else 0.0)
            try:
                intervened_report, delta = self._coherence_graph.simulate(do_int)
                # Store propagated results in twin state for divergence sampling
                twin.snapshot["node_health"] = intervened_report.node_scores
                twin.snapshot["coherence_index"] = intervened_report.coherence_index
            except Exception:
                pass  # coherence graph simulation best-effort

        # 4. Sample divergence over N cycles
        for i in range(self._simulation_cycles):
            actual = self._twin_buffer.actual_snapshot()
            self._calculator.sample(twin.fork_id, actual, twin.snapshot, cycle=i)

        # 5. Compute divergence
        metric = self._calculator.compute(twin.fork_id)
        divergence = metric.weighted_divergence

        # 6. Clean up
        self._calculator.clear(twin.fork_id)
        self._twin_buffer.tick()

        # 7. Decision escalation logic
        if divergence > self._threshold and original_decision == "allow":
            escalated = True
            final_decision = "hold"
            reason = (
                f"Twin simulation divergence ({divergence:.4f}) exceeds "
                f"threshold ({self._threshold}). Escalated from "
                f"allow to hold."
            )
        else:
            escalated = False
            final_decision = original_decision
            if divergence > self._threshold:
                reason = (
                    f"Divergence ({divergence:.4f}) exceeds threshold "
                    f"({self._threshold}), but original decision was "
                    f"'{original_decision}' — not downgrading."
                )
            else:
                reason = (
                    f"Divergence ({divergence:.4f}) within threshold "
                    f"({self._threshold}). Decision: {final_decision}."
                )

        return PreflightVerdict(
            fork_id=twin.fork_id,
            action_type=intervention.action_type,
            divergence=divergence,
            threshold=self._threshold,
            escalated=escalated,
            original_decision=original_decision,
            final_decision=final_decision,
            reason=reason,
        )
