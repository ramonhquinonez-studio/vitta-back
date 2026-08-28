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

- 4 routers legacy siguen sin migrar a `app/modules/` (ver "Pending Migration" abajo) — el resto de los gaps originales (tests, docs, baseline de secrets) ya están resueltos, ver "Applied Foundations".

## Applied Foundations

- existe baseline SDD y guardrails documentados, con una suite de +225 tests;
- la configuración ahora debe operar con placeholders locales explícitos y validaciones de entorno (`app/core/config.py`'s `validate_security_baseline` — rechaza JWT secrets/CORS_ORIGINS placeholder fuera de local).
- **17 de 21 routers ya están migrados** a `app/modules/<feature>/{domain,application,infrastructure,presentation}/`, con su `app/routers/<name>.py` reducido a un wrapper de 1 línea (re-export delgado): `auth`, `appointments`, `billing`, `checkin`, `consultations`, `content_library`, `equivalencies`, `exercise_library`, `me`, `messaging`, `nutrition_lookup`, `nutritionist_profile`, `patients`, `plans`, `recipes`, `recommendations`, `workout_plans`.
- la suite backend incluye guardrails para wrappers y smoke tests de routers modulares.

## Pending Migration

4 routers siguen como archivos standalone en `app/routers/`, sin paquete `app/modules/` propio:

- `users.py` (37 líneas) — solo self-scoped (`get_current_user`), riesgo/prioridad bajos.
- `devices.py` (36 líneas) — igual, self-scoped.
- `google_oauth.py` (130 líneas) — el más grande de los cuatro; flujo de OAuth de Calendar bien aislado, pero vale migrarlo por consistencia.
- `health.py` (12 líneas) — trivial, sin urgencia de migrar.

Ninguno de los cuatro tiene deuda funcional conocida — es puramente inconsistencia estructural frente al resto del código, no bugs.

## Target Shape

```text
app/modules/<feature>/
├── application/
├── domain/
├── infrastructure/
└── presentation/
```

## Refactor Priority

Los primeros seis ítems originales de esta lista ya están resueltos (config/seguridad, convergencia de `me` con `appointments`/`patients`, contratos tipados de `me`, hardening de asignación de planes y de repos/contratos). Lo que queda:

1. Migrar `google_oauth.py` a `app/modules/google_oauth/` — el router legacy más grande restante.
2. Migrar `users.py` y `devices.py` — pequeños, self-scoped, bajo riesgo.
3. `health.py` puede quedarse como está indefinidamente — no hay valor real en migrarlo.

## Rule In Force

Todo módulo nuevo o refactorizado debe nacer en `app/modules/` y no en `app/routers/`.
