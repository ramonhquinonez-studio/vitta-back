# Implementation Plan: Back Auth Module Foundation

**Branch**: `003-back-auth-module-foundation` | **Date**: 2026-03-20 | **Spec**: `specs/003-back-auth-module-foundation/spec.md`

## Summary

Instalar el primer módulo backend real en `app/modules/` usando `auth` como slice piloto, pero conservando el router legacy como fachada compatible.

## Steps

1. Definir entidades y contrato de repositorio en `domain`.
2. Crear `AuthService` en `application`.
3. Crear `MongoAuthRepository` en `infrastructure`.
4. Crear router modular en `presentation` y redirigir `app/routers/auth.py`.
5. Agregar test unitario de `AuthService`.
6. Actualizar docs, roadmap y validar con unittest + py_compile.

## Constraints

- mantener payloads públicos actuales;
- no cambiar wiring global de `app/main.py`;
- no introducir nuevas reglas funcionales fuera del baseline actual.
