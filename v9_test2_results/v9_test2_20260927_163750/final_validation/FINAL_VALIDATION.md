# V9-FULL Final Validation

- configured serving points: **123**
- core serving complete: **True**
- optional capability probes attempted: **True**
- profiles complete: **0 / 45**
- required Native/100G/20G smoke complete: **True**
- full_suite_valid: **False**

## Coverage status counts

- CAPABILITY_BLOCKED: 2
- COMPLETED: 121

## Status semantics

`CAPABILITY_BLOCKED`, `SERVER_START_FAILED`, `SAFETY_SKIPPED`, and `FAILED` remain explicit attempted/non-complete states. Missing configured points are `NOT_RUN`. No state is converted to a metric value of zero.

