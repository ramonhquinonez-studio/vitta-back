# Refactor Specification: [MODULE OR FLOW]

**Feature Branch**: `[###-refactor-name]`
**Created**: [DATE]
**Status**: Draft
**Type**: Refactor

## Objective

- [What architecture or quality problem is being solved]

## In Scope

- [Routers/modules/files included]

## Out of Scope

- [Explicitly list API or behavior changes not allowed]

## Baseline Behavior

- [Current endpoints and outcomes]
- [Known accepted defects in this refactor]

## Target Design

- [Router/service/repository responsibilities]
- [Dependency direction]
- [Persistence and integration boundaries]

## Documentation Impact

- **Module docs to create/update**: [e.g. `docs/modules/architecture.md`]
- **Global docs to create/update**: [e.g. `docs/architecture/ARCHITECTURE_GUARDRAILS.md`]
- **If no documentation update is needed, justify why**: [required explanation]

## Parity Acceptance Criteria

1. Given [scenario], when [request], then [same outcome as baseline]
2. Given [scenario], when [request], then [same outcome as baseline]

## Testing Scope

- service tests:
- router tests:
- repository/integration tests:
- deferred tests and risk:

## Validation

- routers stay thin;
- no direct DB access from new/refactored presentation layer;
- no secrets in code;
- docs updated with final architecture and contract notes.
