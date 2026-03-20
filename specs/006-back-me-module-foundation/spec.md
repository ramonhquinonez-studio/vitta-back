# Refactor Specification: Back Me Module Foundation

**Feature Branch**: `006-back-me-module-foundation`
**Created**: 2026-03-20
**Status**: Draft
**Type**: Refactor

## Objective

Mover `me` desde `app/routers/me.py` a un módulo base en `app/modules/me/`, separando HTTP, application e infrastructure sin cambiar la superficie pública actual.

## In Scope

- crear `app/modules/me/{presentation,application,domain,infrastructure}`;
- mover perfil, citas del paciente, plan activo, mediciones, progreso y contenido clínico al servicio de aplicación;
- dejar `app/routers/me.py` como wrapper delgado;
- agregar test unitario del servicio;
- actualizar docs y roadmap.

## Out of Scope

- converger todavía `me` sobre repositorios de `patients` y `appointments`;
- cambiar payloads públicos;
- refactorizar `plans.py`.

## Baseline Behavior

- `app/routers/me.py` mezcla ownership, acceso a Mongo, parsing de fechas y respuestas;
- el router contiene varias áreas funcionales distintas en un solo archivo;
- no existe módulo `app/modules/me/`.

## Target Design

- `presentation/router.py` solo traduce HTTP <-> application;
- `application/me_service.py` orquesta perfil, citas, progreso y contenido del paciente;
- `infrastructure/mongo_me_repository.py` encapsula acceso a Mongo;
- `domain` define el contrato del repositorio;
- `app/routers/me.py` deja de contener lógica de negocio.

## Documentation Impact

- **Module docs to create/update**: `docs/modules/architecture.md`, `docs/architecture/ARCHITECTURE_GUARDRAILS.md`
- **Global docs to create/update**: `specs/006-back-me-module-foundation/*`

## Parity Acceptance Criteria

1. Given `/me/profile`, `/me/appointments`, `/me/plan/active`, `/me/measurements`, `/me/progress` y los endpoints de contenido clínico, when called, then they still expose the same route surface and same general payload shape.
2. Given patient appointment request/reschedule/cancel, when used, then overlap and pending/canceled behavior remain equivalent.
3. Given the refactored slice, when reviewed, then Mongo access no longer originates from `app/routers/me.py`.

## Validation

- `python -m unittest tests.test_me_service`
- `python -m py_compile` touched me files
