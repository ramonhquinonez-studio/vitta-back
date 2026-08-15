# Feature Specification: Back Auth Registration And Recovery

**Feature Branch**: `009-back-auth-registration-and-recovery`
**Created**: 2026-08-12
**Status**: Draft
**Type**: Feature

## Objective

Cerrar el flujo de auth del lado backend: `POST /auth/register` dejó de crear cuentas huérfanas (sin `patients` ligado) y ganó un mecanismo de invitación por código; se agregan `forgot-password`/`reset-password` sin depender de un proveedor de correo todavía inexistente.

## In Scope

- Colección `invite_codes` (código único, dueño, expiración, uso único) y `POST /patients/invite-codes` para que un pro genere uno.
- `AuthService.register` exige `invite_code`, crea el `users` con `role="patient"` y su `patients` ligado al `owner_id` del código, y consume el código.
- Token de reset de contraseña sin estado (JWT corto con guarda derivada del `password_hash` actual, invalidado automáticamente al usarse).
- `POST /auth/forgot-password` (respuesta genérica siempre, sin filtrar qué correos existen) y `POST /auth/reset-password`.
- Código de invitación demo (`DEMO2026`) en `seed_dev.py` para poder probar el registro sin acceso al lado "pro".

## Out of Scope

- Envío real de correo: no hay integración SMTP/proveedor todavía. Fuera de `local`/`dev`, `forgot-password` no expone el token en la respuesta (queda inutilizable hasta que exista esa integración).
- Revocación de refresh tokens en logout (queda fuera del alcance decidido).
- Verificación de correo electrónico.

## Baseline Behavior

- `POST /auth/register` creaba un `users` con `role="user"` sin ningún `patients` ligado; cualquier cliente que iniciara sesión después quedaba sin perfil de paciente.
- No existía forma de invitar/ligar un paciente a un `owner_id` fuera del seed script o del endpoint pro-side `POST /patients`.
- No existía `forgot-password`/`reset-password` en ninguna forma.

## Target Design

- `invite_codes`: `{code, owner_id, created_at, expires_at, used_at, used_by_user_id}`, índice único en `code`.
- El token de reset lleva `sub`, `type="password_reset"` y `pwd_guard` (digest corto del `password_hash` vigente al emitirlo); al resetear, el hash cambia y el guard deja de coincidir, lo que implementa "un solo uso" sin tabla extra.
- `ForgotPasswordOut.reset_token` solo se rellena cuando `APP_ENV` no es `prod`/`production`/`staging`.

## Documentation Impact

- **Module docs to create/update**: ninguno nuevo (backend no mantiene `docs/modules/architecture.md` propio en este repo; ver `nutri_app`'s spec para el lado consumidor).
- **Global docs to create/update**: `specs/009-back-auth-registration-and-recovery/*`.

## Parity Acceptance Criteria

1. Given un código de invitación válido, when un usuario se registra con él, then se crea `users` (`role=patient`) y `patients` ligado al dueño del código, y el código queda consumido.
2. Given un código inválido, usado o expirado, when se intenta registrar, then la API responde 404 y no se crea ningún usuario.
3. Given un correo registrado, when se pide `forgot-password`, then se emite un token válido por 30 minutos que `reset-password` acepta una sola vez.
4. Given un correo no registrado, when se pide `forgot-password`, then la respuesta es idéntica a la de un correo válido (sin token).

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`
