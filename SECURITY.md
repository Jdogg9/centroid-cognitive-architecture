# Security Policy

Centroid is a research and developer framework. Security reports are welcome,
especially for issues involving unsafe tool execution, credential exposure,
hidden persistence, or bypass of approval gates.

## Supported Versions

| Version | Supported |
| --- | --- |
| `main` | Yes |
| `v0.1.x` | Yes |

## Reporting A Vulnerability

Open a private security advisory on GitHub when available. If that is not
available, open a minimal public issue that does not include exploit details or
secrets, and request a private contact path.

## Security Scope

Relevant issues include:

- credential or token exposure
- unsafe file writes or destructive actions
- bypassable permission gates
- uncontrolled tool execution
- hidden persistence or undeclared background behavior
- shutdown non-compliance
- audit log tampering
- memory policy violations

## Safety Boundary

Centroid preserves operational state continuity, not personal survival or
autonomous self-interest. Security fixes should strengthen bounded autonomy,
human override, transparent memory policies, auditability, and shutdown
compliance.

