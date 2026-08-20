# Tasks: Minimal Hydration Tracking

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `me/domain/repositories.py`: `get_hydration_today` / `add_hydration` en el Protocol.
- [x] T003 `me/infrastructure/mongo_me_repository.py`: implementación contra `hydration_logs`.
- [x] T004 `me/application/me_service.py`: `get_hydration` / `add_hydration`.
- [x] T005 `me/presentation/router.py`: `GET`/`POST /hydration`.
- [x] T006 Tests nuevos en `test_me_service.py`.

## Phase 3: Validation

- [x] T007 Suite completa → 103/103 verde.
- [x] T008 `curl` cubriendo: default sin registros, acumulación de +250 x2, clamp inferior (-1000), clamp superior (+5000).

## Evidence

- Suite completa: 103/103, verde.
- `curl` contra backend local real: `GET` inicial → `{"current_ml": 0, "target_ml": 2000}`; dos `POST {"delta_ml": 250}` → 250, luego 500; `GET` posterior confirma 500 persistido; `POST {"delta_ml": -1000}` → clamp a 0; `POST {"delta_ml": 5000}` → clamp a 2000.
