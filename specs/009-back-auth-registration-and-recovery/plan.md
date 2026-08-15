# Implementation Plan: Back Auth Registration And Recovery

**Branch**: `009-back-auth-registration-and-recovery` | **Date**: 2026-08-12 | **Spec**: `specs/009-back-auth-registration-and-recovery/spec.md`

## Summary

Extender el módulo `auth` y el módulo `patients` para que el registro de pacientes quede completo (cuenta + perfil ligado) vía invitación, y agregar recuperación de contraseña sin backend de correo.

## Steps

1. `core/security.py`: `create_password_reset_token`/`decode_password_reset_token`/`password_reset_guard_matches` (JWT sin estado, guarda basada en `password_hash`).
2. `schemas/auth.py`: `RegisterIn.invite_code`, `InviteCodeOut`, `ForgotPasswordIn/Out`, `ResetPasswordIn`.
3. `modules/auth`: `AuthRepository` gana `get_invite_code`/`consume_invite_code`/`create_patient_for_user`/`update_password_hash`; `MongoAuthRepository` los implementa tocando `invite_codes`/`patients`/`users`; `AuthService.register` valida+consume el código y crea el `patients`; `AuthService.forgot_password`/`reset_password` nuevos.
4. `modules/patients`: `PatientsRepository.create_invite_code`, generación de código corto sin caracteres ambiguos, `POST /patients/invite-codes`.
5. `db/init_indexes.py`: índice único en `invite_codes.code`.
6. `seed_dev.py`: código demo `DEMO2026` ligado al pro de seed.
7. `tests/test_auth_service.py`: fake repository extendido + casos nuevos (código inválido/usado/expirado, forgot/reset, reuso de token).

## Constraints

- Sin nueva colección para tokens de reset: todo vía JWT con guarda embebida, consistente con el patrón sin estado ya usado para access/refresh.
- `forgot-password` responde siempre igual para no filtrar qué correos existen; el token de dev solo viaja fuera de `prod`/`staging`.
- No se toca la revocación de refresh tokens en logout (decidido fuera de alcance).
