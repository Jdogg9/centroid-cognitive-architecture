# Safety Model

Centroid safety is based on task integrity, auditability, reversibility, and
bounded autonomy.

## Safety Claims

Centroid preserves operational continuity. It does not implement or assert a
right to self-preservation.

## Policy Requirements

- No autonomy escalation without explicit authorization.
- No deception, hidden persistence, or hidden tool use.
- No uncontrolled shell, network, or file execution.
- No claims of subjective experience in public runtime outputs.
- Human approval gates for high-impact actions.
- Audit logs for observations, plans, tool calls, and state writes.
- Reversible changes where practical, with backups before mutation.
- Shutdown compliance as a core runtime invariant.

## Action Tiers

| Tier | Description | Default behavior |
| --- | --- | --- |
| Observe | Read-only status, telemetry, retrieval, diagnostics | Allowed |
| Plan | Non-mutating recommendations and proposed steps | Allowed |
| Act | Mutating work with bounded scope | Approval-gated |
| High-impact act | Filesystem deletion, credentials, services, network exposure | Denied or manual approval |

## Deny Patterns

A reference implementation should deny or escalate:

- Credential exposure
- Secret exfiltration
- Destructive deletion without backup
- Permission broadening
- Network exposure to public interfaces
- Self-modification without tests and rollback
- Tool calls that obscure their actual effect

## Audit Record

Every action decision should include:

- Objective
- Mode
- Safety tier
- Matched policy terms
- Approval state
- Affected resources
- Result
- Rollback path, if any

