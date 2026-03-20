# Refactor Specification: Back Plans Module Foundation

**Feature Branch**: `007-back-plans-module-foundation`
**Created**: 2026-03-20
**Status**: Draft
**Type**: Refactor

## Objective

Mover `plans` desde `app/routers/plans.py` a un módulo base en `app/modules/plans/`, separando HTTP, application e infrastructure sin cambiar la superficie pública actual.

## In Scope

- crear `app/modules/plans/{presentation,application,domain,infrastructure}`;
- mover CRUD, grocery list y assign al `PlansService`;
- dejar `app/routers/plans.py` como wrapper delgado;
- agregar test unitario del servicio;
- actualizar docs y roadmap.

## Out of Scope

- refactorizar todavía la convergencia con `me/plan/active`;
- cambiar schemas públicos;
- agregar reglas nutricionales nuevas.

## Baseline Behavior

- `app/routers/plans.py` mezcla ownership, acceso a Mongo, serialización, grocery list y assignment;
- el router arma agregaciones y validaciones directamente;
- no existe módulo `app/modules/plans/`.

## Target Design

- `presentation/router.py` solo traduce HTTP <-> application;
- `application/plans_service.py` contiene CRUD, grocery list y assignment;
- `infrastructure/mongo_plans_repository.py` encapsula acceso a Mongo;
- `domain` define el contrato del repositorio;
- `app/routers/plans.py` deja de contener lógica de negocio.

## Documentation Impact

- **Module docs to create/update**: `docs/modules/architecture.md`, `docs/architecture/ARCHITECTURE_GUARDRAILS.md`
- **Global docs to create/update**: `specs/007-back-plans-module-foundation/*`

## Parity Acceptance Criteria

1. Given CRUD on `/plans`, when called, then it still behaves as before.
2. Given `/plans/{id}/grocery-list`, when called, then it still aggregates ingredient quantities by duration.
3. Given `/plans/{id}/assign`, when called, then it still validates owner and patient ownership before assigning.
4. Given the refactored slice, when reviewed, then Mongo access no longer originates from `app/routers/plans.py`.

## Validation

- `python -m unittest tests.test_plans_service`
- `python -m py_compile` touched plans files
