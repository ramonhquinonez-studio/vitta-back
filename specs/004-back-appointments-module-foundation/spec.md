# Refactor Specification: Back Appointments Module Foundation

**Feature Branch**: `004-back-appointments-module-foundation`
**Created**: 2026-03-20
**Status**: Draft
**Type**: Refactor

## Objective

Extraer el router de `appointments` a un módulo base en `app/modules/appointments/`, separando HTTP, orquestación, persistencia y sync de Google Calendar.

## In Scope

- crear `app/modules/appointments/{presentation,application,domain,infrastructure}`;
- mover list/create/get/update/delete al servicio de aplicación;
- encapsular Mongo y Google Calendar en infraestructura;
- dejar `app/routers/appointments.py` como wrapper delgado;
- agregar test unitario del servicio;
- actualizar docs y roadmap.

## Out of Scope

- refactorizar los endpoints de citas en `me.py`;
- cambiar el contrato público del router;
- agregar notificaciones push o nueva lógica de reminder.

## Baseline Behavior

- `app/routers/appointments.py` mezcla schemas, validación, queries Mongo, serialización y Google Calendar;
- los filtros de overlap viven embebidos en el router;
- el sync con Google está acoplado a los handlers HTTP.

## Target Design

- `presentation/router.py` solo traduce HTTP <-> application;
- `application/appointments_service.py` orquesta overlap, CRUD y sync best-effort;
- `infrastructure/mongo_appointments_repository.py` encapsula queries/serialización Mongo;
- `infrastructure/google_calendar_gateway.py` encapsula integración Calendar;
- `app/routers/appointments.py` deja de contener lógica de negocio.

## Documentation Impact

- **Module docs to create/update**: `docs/modules/architecture.md`, `docs/architecture/ARCHITECTURE_GUARDRAILS.md`
- **Global docs to create/update**: `specs/004-back-appointments-module-foundation/*`

## Parity Acceptance Criteria

1. Given list/create/get/update/delete on `/appointments`, when called, then they still expose the same route surface and overlap conflict payload.
2. Given Google Calendar sync failures, when they happen, then the API still returns success for CRUD as before.
3. Given the refactored slice, when reviewed, then Mongo and Calendar logic no longer originate from `app/routers/appointments.py`.

## Validation

- `python -m unittest tests.test_appointments_service`
- `python -m py_compile` touched appointments files
