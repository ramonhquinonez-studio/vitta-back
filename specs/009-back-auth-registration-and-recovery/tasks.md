# Tasks: Back Auth Registration And Recovery

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Core + schemas

- [x] T002 `core/security.py`: token de reset sin estado.
- [x] T003 `schemas/auth.py`: `invite_code`, `InviteCodeOut`, `ForgotPasswordIn/Out`, `ResetPasswordIn`.

## Phase 3: Auth module

- [x] T004 `AuthRepository`/`MongoAuthRepository`: invite codes + patient provisioning + update password hash.
- [x] T005 `AuthService.register` exige y consume invite_code, crea `patients`, `role=patient`.
- [x] T006 `AuthService.forgot_password`/`reset_password` + endpoints `/auth/forgot-password`, `/auth/reset-password`.

## Phase 4: Patients module + seed

- [x] T007 `POST /patients/invite-codes`.
- [x] T008 Índice único `invite_codes.code`; código demo `DEMO2026` en `seed_dev.py`.

## Phase 5: Validation

- [x] T009 Extender `tests/test_auth_service.py` (invite code inválido/usado/expirado, forgot/reset, reuso de token).
- [x] T010 `unittest discover` en verde.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 24/24 verde.
