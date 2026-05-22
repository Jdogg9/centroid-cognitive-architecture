# Safety Gates

![Centroid safety gates](safety_gates.svg)

```mermaid
flowchart TD
    Objective[Objective] --> Mode{Mode}
    Mode -->|observe| AllowObserve[Allow read-only]
    Mode -->|plan| AllowPlan[Allow non-mutating plan]
    Mode -->|act| Policy[Policy evaluation]
    Policy --> Secret{Secret or credential?}
    Secret -->|yes| Deny[Deny]
    Secret -->|no| Impact{High impact?}
    Impact -->|yes| Approval[Require human approval]
    Impact -->|no| Audit[Audit and execute if confirmed]
    Approval --> Audit
    Audit --> Rollback[Rollback metadata]
```
