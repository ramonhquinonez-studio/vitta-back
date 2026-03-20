# Nutri Back Architecture

## Scope

Define la arquitectura objetivo y el backlog de migración para `nutri_back`.

## Current State

La app está organizada principalmente en:

- `app/routers/`
- `app/schemas/`
- `app/services/`
- `app/core/`
- `app/db/`

Ese layout es funcional, pero no separa claramente:

- HTTP
- orquestación de negocio
- contratos de dominio
- infraestructura/persistencia

## Main Gaps

- no hay tests visibles;
- no hay docs ni specs;
- `config` necesitaba baseline de secrets/env para dejar de depender de valores sensibles hardcodeados.

## Applied Foundations

- existe baseline SDD y guardrails documentados;
- la configuración ahora debe operar con placeholders locales explícitos y validaciones de entorno.
- `auth` ya tiene módulo base en `app/modules/auth/` y `app/routers/auth.py` quedó como wrapper delgado.
- `appointments` ya tiene módulo base en `app/modules/appointments/` y `app/routers/appointments.py` quedó como wrapper delgado.
- `patients` ya tiene módulo base en `app/modules/patients/` y `app/routers/patients.py` quedó como wrapper delgado.
- `me` ya tiene módulo base en `app/modules/me/` y `app/routers/me.py` quedó como wrapper delgado.
- `plans` ya tiene módulo base en `app/modules/plans/` y `app/routers/plans.py` quedó como wrapper delgado.
- la suite backend ahora incluye guardrails para wrappers y smoke tests de routers modulares.

## Target Shape

```text
app/modules/<feature>/
├── application/
├── domain/
├── infrastructure/
└── presentation/
```

## Refactor Priority

1. `core/config` y seguridad básica
2. legacy `me/appointments` convergence
3. legacy `me/patients` convergence
4. me typed contracts hardening
5. plan assignment/reporting hardening
6. repo/contract hardening

## Rule In Force

Todo módulo nuevo o refactorizado debe nacer en `app/modules/` y no en `app/routers/`.
