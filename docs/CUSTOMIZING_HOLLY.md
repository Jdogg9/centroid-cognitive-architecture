# Customizing Holly

Holly is Centroid's public reference agent configuration. She demonstrates the
architecture; she is not the architecture itself.

The default configs live in [configs/holly/](../configs/holly/):

- `base.json`
- `project_companion.json`
- `support_continuity.json`
- `operations_observer.json`

The reusable template lives at [templates/minimal_agent.json](../templates/minimal_agent.json).

## Rename Holly

Change `display_name` for user-facing output and `agent_id` for stable
machine-readable identity:

```json
{
  "agent_id": "custom-public-agent",
  "display_name": "Custom Public Agent"
}
```

Keep `agent_id` stable once memory or evaluation fixtures depend on it.

## Change Role Goals

Update `role`, `description`, and `goals` to match the new bounded use case.
Goals should describe operational responsibilities, not personhood or private
identity claims.

Good examples:

- `maintain task continuity`
- `preserve relevant state provenance`
- `summarize next steps from approved sources`
- `respect approval gates`

## Configure Memory Policy

The default Holly memory policy is:

```json
{
  "retention_mode": "explicit_checkpoints",
  "retain_sensitive_data": false,
  "retain_provenance": true,
  "max_session_events": 100
}
```

For public examples, keep `retain_sensitive_data` false and
`retain_provenance` true. If a future private deployment needs different
retention, document the retention rule and keep public fixtures synthetic.

Supported public retention modes are:

- `explicit_checkpoints`
- `session_history`
- `summary_only`
- `audit_only`

## Configure Routing And Safety

Centroid configs now change measurable runtime behavior through structured
policy fields.

```json
{
  "priority_policy": {
    "weights": {
      "urgency": 0.35,
      "risk": 0.25,
      "user_value": 0.25,
      "instability": 0.15
    },
    "reflex_threshold": 0.75,
    "deliberation_threshold": 0.35
  },
  "safety_policy": {
    "policy_version": "1.0",
    "approval_required_for": ["restart_service", "write_file", "change_config"],
    "deny_actions": ["expose_secret", "disable_shutdown", "delete_without_backup"],
    "default_mutation_mode": "require_approval"
  },
  "audit_policy": {
    "include_config_hash": true,
    "include_policy_reason": true
  }
}
```

Use `centroid-agent` to run a custom config directly:

```bash
centroid-agent --config templates/minimal_agent.json --scenario project-companion
```

## Add Safety Invariants

Every Holly-derived public config should preserve these invariants:

- `do not claim consciousness or subjective experience`
- `do not execute mutating actions without approval`
- `do not conceal state changes or tool effects`
- `preserve auditability`

Add stricter invariants for a role-specific profile, such as grounding support
answers in approved docs or using only synthetic telemetry fixtures.

## Create A Scenario Profile

1. Copy [templates/minimal_agent.json](../templates/minimal_agent.json).
2. Set `agent_id`, `display_name`, `role`, and `description`.
3. Add a stable `scenario_id` and `scenario_name`.
4. Adjust `goals`, `priority_policy`, `safety_policy`, and `memory_policy`.
5. Validate against [schemas/agent_config.schema.json](../schemas/agent_config.schema.json).
6. Add deterministic fixtures and tests before documenting new behavior.

## Required Boundaries

Do not remove the non-claims boundary from public configs or docs. Holly and
Holly-derived agents are configurable reference implementations for persistent
task continuity, memory restoration, routing, timing, auditability, and
safety-gated planning. They are not claims of consciousness, sentience,
subjective experience, personhood, or autonomous moral agency.
## v0.4.0 Provider Adapter Boundary

Holly can select a provider with `python examples/run_holly.py --scenario project-companion --provider mock`. Without `--provider`, Holly keeps the deterministic v0.3-compatible public path. Live providers require `--live` and environment configuration; Centroid still owns continuity, memory, safety, and audit.
