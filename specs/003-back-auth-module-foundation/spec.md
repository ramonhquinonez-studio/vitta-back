# Refactor Specification: Back Auth Module Foundation

**Feature Branch**: `003-back-auth-module-foundation`
**Created**: 2026-03-20
**Status**: Draft
**Type**: Refactor

## Objective

Mover `auth` desde `app/routers/auth.py` a un módulo base en `app/modules/auth/`, separando HTTP, application, domain e infrastructure sin cambiar el contrato público actual.

## In Scope

- crear `app/modules/auth/{presentation,application,domain,infrastructure}`;
- mover registro, login y refresh a `AuthService` + `MongoAuthRepository`;
- dejar `app/routers/auth.py` como wrapper delgado de compatibilidad;
- agregar test unitario del servicio de auth;
- actualizar docs y roadmap.

## Out of Scope

- refactorizar `users.py` o `core/deps.py`;
- introducir refresh token persistence o logout server-side;
- cambiar rutas o payloads públicos de `/auth`.

## Baseline Behavior

- `app/routers/auth.py` mezcla HTTP, acceso a Mongo, hashing y emisión de tokens;
- el router construye y serializa respuestas directamente;
- no existe módulo `app/modules/auth/`.

## Target Design

- `presentation/router.py` solo traduce HTTP <-> application;
- `application/auth_service.py` contiene reglas de registro/login/refresh;
- `infrastructure/mongo_auth_repository.py` encapsula acceso a Mongo;
- `domain` define entidades y contrato de repositorio;
- `app/routers/auth.py` deja de contener lógica de negocio.

## Documentation Impact

- **Module docs to create/update**: `docs/modules/architecture.md`, `docs/architecture/ARCHITECTURE_GUARDRAILS.md`
- **Global docs to create/update**: `specs/003-back-auth-module-foundation/*`

## Parity Acceptance Criteria

1. Given `/auth/register`, when called with a new email, then it still creates the user and returns `id` plus `email`.
2. Given `/auth/login`, when credentials are valid, then it still returns `access_token`, `refresh_token` and `token_type`.
3. Given `/auth/refresh`, when the refresh token is valid, then it still returns a fresh token pair.
4. Given the refactored slice, when reviewed, then Mongo access no longer originates from `app/routers/auth.py`.

## Validation

- `python -m unittest tests.test_auth_service`
- `python -m py_compile` touched auth files
