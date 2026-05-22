# Agent Templates

Templates show how to create a Centroid-based reference agent without changing
the core architecture modules.

## Minimal Agent

Start with `minimal_agent.json`, then change:

- `agent_id` to a stable machine-readable identifier.
- `display_name` to the public name shown in demos or logs.
- `role` and `description` to describe the bounded implementation purpose.
- `goals` to match the role-specific tasks.
- `memory_policy` to match retention and provenance requirements.

Keep the required invariants unless you are deliberately building a stricter
profile:

- no consciousness or subjective-experience claims
- no mutating execution without approval
- no hidden state changes or tool effects
- preserved auditability

Validate custom configs against
`schemas/agent_config.schema.json` and load them with
`core.agent_config.load_agent_config`.
