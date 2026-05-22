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
  "default_retention": "session_and_explicit_checkpoints",
  "store_sensitive_data": false,
  "require_provenance": true
}
```

For public examples, keep `store_sensitive_data` false and
`require_provenance` true. If a future private deployment needs different
retention, document the retention rule and keep public fixtures synthetic.

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
4. Adjust `goals`, `priority_policy`, and `safety_policy`.
5. Validate against [schemas/agent_config.schema.json](../schemas/agent_config.schema.json).
6. Add deterministic fixtures and tests before documenting new behavior.

## Required Boundaries

Do not remove the non-claims boundary from public configs or docs. Holly and
Holly-derived agents are configurable reference implementations for persistent
task continuity, memory restoration, routing, timing, auditability, and
safety-gated planning. They are not claims of consciousness, sentience,
subjective experience, personhood, or autonomous moral agency.
