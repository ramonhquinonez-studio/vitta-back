# Refactor Specification: Vitta Back Architecture Bootstrap

**Feature Branch**: `001-vitta-architecture-bootstrap`
**Created**: 2026-03-20
**Status**: Draft
**Type**: Refactor

## Objective

Instalar la base SDD del backend y documentar el roadmap de migración desde la estructura actual hacia una arquitectura modular equivalente a `fidelity_back`.

## In Scope

- crear hub documental `docs/`;
- crear política SDD;
- crear guardrails arquitectónicos iniciales;
- documentar gaps actuales;
- crear `specs/001-vitta-architecture-bootstrap/`;
- dejar template para refactors futuros.

## Out of Scope

- mover código a `app/modules/`;
- refactorizar routers actuales;
- introducir tests todavía;
- cambiar contratos API.

## Baseline Behavior

- `nutri_back` funciona principalmente desde `app/routers/*`;
- los routers contienen lógica de negocio y acceso a Mongo;
- no hay capa modular equivalente a `fidelity_back`;
- no hay docs de arquitectura visibles;
- no hay tests visibles;
- `app/core/config.py` contiene secretos/defaults sensibles en código.

## Findings Snapshot

1. `app/core/config.py` contiene `JWT_SECRET`, `JWT_REFRESH_SECRET`, `GOOGLE_CLIENT_SECRET` hardcodeados.
2. `app/routers/appointments.py` mezcla HTTP, validación, Mongo, serialización, overlap rules y Google Calendar.
3. `app/routers/auth.py`, `patients.py`, `plans.py`, `me.py` siguen el mismo patrón de router grueso.
4. No existe estructura `app/modules/<feature>/application/domain/infrastructure/presentation`.
5. No existe base SDD ni documentación operativa/arq propia del repo.

## Documentation Impact

- **Module docs to create/update**: `docs/modules/architecture.md`
- **Global docs to create/update**: `docs/README.md`, `docs/SDD_DOCUMENTATION_POLICY.md`, `docs/architecture/ARCHITECTURE_GUARDRAILS.md`, `.specify/templates/refactor-spec-template.md`
- **Baseline/parity evidence docs impacted**: `specs/001-vitta-architecture-bootstrap/plan.md`, `tasks.md`

## Parity Acceptance Criteria

1. Given the current repo, when the bootstrap is reviewed, then the target modular architecture and migration priorities are explicitly documented.
2. Given future backend refactors, when a change starts, then the repo already has a minimal SDD and guardrail baseline.

## Validation

- confirmar creación de docs/specs/templates;
- revisar consistencia del diagnóstico contra el código actual;
- cero cambio funcional.
