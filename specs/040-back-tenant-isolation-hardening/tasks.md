# Tasks: Tenant Isolation & Authorization Hardening

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `mongo_appointments_repository.py`: `delete_for_owner`/`set_google_event_id` con filtro `owner_id`.
- [x] T003 `appointments_service.py`: pasar `owner_id` en ambos call sites de `set_google_event_id`.
- [x] T004 `app/core/deps.py`: `require_role`.
- [x] T005 Aplicar `require_role("nutritionist")` a los routers nutricionista-only y a los endpoints de escritura de `equivalencies`/`content_library`.
- [x] T006 `hydration_logs`: `owner_id` en `add_hydration` (dominio + Mongo + servicio).
- [x] T007 `app/core/rate_limit.py` + índices TTL + wiring en `/auth/register` y `/auth/register-nutritionist`.
- [x] T008 Tests nuevos: `test_appointments_service.py` (2), `test_require_role.py` (3).

## Phase 3: Validation

- [x] T009 Suite completa → 132/132 verde (previo a `041`).
- [x] T010 Verificación en vivo: token nutricionista vs paciente contra rutas gateadas, rutas `/me` y `/equivalencies` de lectura sin afectar, rate limit real (11 intentos → 429).

## Evidence

- Suite completa: 132/132 verde en este punto.
- Verificación en vivo: nutricionista `200` en `/patients`, paciente `403`; `/me/appointments` y `/equivalencies/groups` `200` para paciente; `/equivalencies/foods` POST `403` para paciente; 10 registros exitosos + 1 `429` en el intento 11.
