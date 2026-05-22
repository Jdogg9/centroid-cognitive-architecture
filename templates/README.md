# Agent Templates

Templates show how to create a Centroid-based reference agent without changing
the core architecture modules.

## Minimal Agent

Start with `minimal_agent.json`, then change:

- `agent_id` to a stable machine-readable identifier.
- `config_version` when you intentionally revise the public config contract.
- `display_name` to the public name shown in demos or logs.
- `role` and `description` to describe the bounded implementation purpose.
- `goals` to match the role-specific tasks.
- `memory_policy` to match retention and provenance requirements.
- `priority_policy`, `safety_policy`, and `audit_policy` to change runtime behavior.

Keep the required invariants unless you are deliberately building a stricter
profile:

- no consciousness or subjective-experience claims
- no mutating execution without approval
- no hidden state changes or tool effects
- preserved auditability

Validate custom configs against
`schemas/agent_config.schema.json` and load them with
`core.agent_config.load_agent_config`, then run them with:

```bash
centroid-agent --config templates/minimal_agent.json --scenario project-companion
```
