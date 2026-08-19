# Tasks: Invite Code Preview (Unauthenticated)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/auth.py`: `InvitePreviewOut`.
- [x] T003 `auth/domain/repositories.py`: `get_patient_name` en el Protocol.
- [x] T004 `auth/infrastructure/mongo_auth_repository.py`: implementación de `get_patient_name`.
- [x] T005 `auth/application/auth_service.py`: `preview_invite_code`.
- [x] T006 `auth/presentation/router.py`: `GET /invite-codes/{code}`.
- [x] T007 Tests nuevos en `test_auth_service.py`.

## Phase 3: Validation

- [x] T008 Suite completa → 95/95 verde.
- [x] T009 `curl` cubriendo: sin escopar, escopado, desconocido, usado, expirado, insensible a mayúsculas.

## Evidence

- Suite completa: 95/95, verde.
- `curl` contra backend local real: código sin escopar → `{"valid": true, "scoped": false, "nutritionist_name": "..."}`; código escopado → `{"valid": true, "scoped": true, "patient_name": "...", "nutritionist_name": "..."}`; código desconocido/usado/expirado → `{"valid": false}` en los tres casos; código en minúsculas → resuelto igual que en mayúsculas.
