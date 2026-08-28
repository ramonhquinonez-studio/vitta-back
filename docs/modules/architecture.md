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

Ninguno pendiente en este frente — los 21 routers ya están migrados (ver "Applied Foundations"). El resto de los gaps originales (tests, docs, baseline de secrets) también están resueltos.

## Applied Foundations

- existe baseline SDD y guardrails documentados, con una suite de +227 tests;
- la configuración ahora debe operar con placeholders locales explícitos y validaciones de entorno (`app/core/config.py`'s `validate_security_baseline` — rechaza JWT secrets/CORS_ORIGINS placeholder fuera de local).
- **Los 21 routers están migrados** a `app/modules/<feature>/{domain,application,infrastructure,presentation}/`, cada `app/routers/<name>.py` reducido a un wrapper de 1 línea (re-export delgado): `auth`, `appointments`, `billing`, `checkin`, `consultations`, `content_library`, `equivalencies`, `exercise_library`, `me`, `messaging`, `nutrition_lookup`, `nutritionist_profile`, `patients`, `plans`, `recipes`, `recommendations`, `workout_plans`, y — última tanda, `067-back-router-migration` — `users`, `devices`, `google_oauth`, `health`.
  - `health` es el único módulo sin capas `domain/application/infrastructure`: no hay lógica de negocio ni persistencia que separar (solo devuelve config estática), así que solo tiene `presentation/router.py`. El resto de los 21 sí tiene las cuatro capas.
  - `google_oauth` sigue el mismo patrón que `billing` (que aísla el SDK de Stripe en `infrastructure/stripe_billing_provider.py`): el wrapper del SDK de Google (`Flow`, intercambio de tokens, revocación HTTP) vive en `infrastructure/google_oauth_client.py`, separado de la orquestación (emisión/validación del JWT de `state`, flujo de conexión/desconexión) en `application/google_oauth_service.py`.
- la suite backend incluye guardrails para wrappers y smoke tests de routers modulares (`test_router_wrapper_guardrails.py` cubre los 21, aunque su lista interna aún no incluye `billing`/`checkin`/`messaging`/`workout_plans`/`exercise_library`/`nutrition_lookup` — deuda de documentación menor, no funcional, dejada tal cual por ahora).

## Target Shape

```text
app/modules/<feature>/
├── application/
├── domain/
├── infrastructure/
└── presentation/
```

## Refactor Priority

Todos los ítems originales de esta lista están resueltos (config/seguridad, convergencia de `me` con `appointments`/`patients`, contratos tipados de `me`, hardening de asignación de planes y de repos/contratos, y la migración de los últimos 4 routers). Sin refactors estructurales pendientes por ahora — ver `specs/SPEC_ROADMAP.md`'s "Next Recommended Specs" para el resto del backlog (logging estructurado, etc.).

## Rule In Force

Todo módulo nuevo o refactorizado debe nacer en `app/modules/` y no en `app/routers/`.
