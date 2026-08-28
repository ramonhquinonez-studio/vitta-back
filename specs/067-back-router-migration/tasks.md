# Tasks: Migrate the 4 Remaining Fat Routers

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/modules/health/` (solo `presentation/router.py`) + wrapper.
- [x] T003 `app/modules/users/` (4 capas) + wrapper.
- [x] T004 `app/modules/devices/` (4 capas) + wrapper.
- [x] T005 `app/modules/google_oauth/` (4 capas, cliente de Google aislado en `infrastructure/`) + wrapper.
- [x] T006 `test_router_wrapper_guardrails.py`: 4 entradas nuevas.
- [x] T007 `docs/modules/architecture.md`: 21/21 routers migrados.

## Phase 3: Validation

- [x] T008 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 227/227 verde.
- [x] T009 Verificación en vivo de los 9 endpoints migrados, con limpieza posterior.

## Evidence

- Suite completa: 227/227 verde (sin tests nuevos más allá de la extensión del guardrail — refactor puro).
- En vivo, todos contra la cuenta demo sembrada:
  - `GET /healthz` → `{"status":"ok"}`
  - `GET /version` → `{"app":"NutriAPI","version":"0.1.0","env":"local"}`
  - `GET /users/me` → perfil correcto
  - `POST /devices/register` → `{"ok":true}` (registro de QA eliminado tras la verificación)
  - `GET /google/status` → `{"connected":false}`
  - `POST /google/oauth/start_url` → URL de autorización de Google real y correctamente firmada
  - `DELETE /google/disconnect` → `{"ok":true,"disconnected":true,"msg":"No tokens stored"}`
  - `POST /devices/test` → reveló un bug preexistente y no relacionado en `app/core/notify.py` (`send_multicast` no existe en el SDK instalado de `firebase_admin`), confirmado ajeno a esta migración por el traceback.
