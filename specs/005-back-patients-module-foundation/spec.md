# Refactor Specification: Back Patients Module Foundation

**Feature Branch**: `005-back-patients-module-foundation`
**Created**: 2026-03-20
**Status**: Draft
**Type**: Refactor

## Objective

Mover `patients` desde `app/routers/patients.py` a un módulo base en `app/modules/patients/`, separando HTTP, application, domain e infrastructure sin cambiar el contrato público actual.

## In Scope

- crear `app/modules/patients/{presentation,application,domain,infrastructure}`;
- mover list/create/get/update/delete a `PatientsService` + `MongoPatientsRepository`;
- dejar `app/routers/patients.py` como wrapper delgado;
- agregar test unitario del servicio;
- actualizar docs y roadmap.

## Out of Scope

- refactorizar todavía la porción de pacientes dentro de `me.py`;
- cambiar schemas públicos existentes;
- agregar validaciones de negocio nuevas fuera del baseline actual.

## Baseline Behavior

- `app/routers/patients.py` mezcla ownership, paginación, acceso a Mongo y serialización;
- el router arma filtros y respuestas directamente;
- no existe módulo `app/modules/patients/`.

## Target Design

- `presentation/router.py` solo traduce HTTP <-> application;
- `application/patients_service.py` contiene CRUD y ownership flow;
- `infrastructure/mongo_patients_repository.py` encapsula acceso a Mongo;
- `domain` define entidad y contrato de repositorio;
- `app/routers/patients.py` deja de contener lógica de negocio.

## Documentation Impact

- **Module docs to create/update**: `docs/modules/architecture.md`, `docs/architecture/ARCHITECTURE_GUARDRAILS.md`
- **Global docs to create/update**: `specs/005-back-patients-module-foundation/*`

## Parity Acceptance Criteria

1. Given `/patients`, when listing with pagination and query, then it still returns the same page shape.
2. Given create/get/update/delete on `/patients/{id}`, when called, then they still behave as before.
3. Given the refactored slice, when reviewed, then Mongo access no longer originates from `app/routers/patients.py`.

## Validation

- `python -m unittest tests.test_patients_service`
- `python -m py_compile` touched patients files
