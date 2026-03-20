# Implementation Plan: Back Me Module Foundation

**Branch**: `006-back-me-module-foundation` | **Date**: 2026-03-20 | **Spec**: `specs/006-back-me-module-foundation/spec.md`

## Summary

Instalar el módulo `me` como slice backend para sacar del router toda la lógica de paciente autenticado sin intentar todavía la convergencia completa con otros módulos.

## Steps

1. Definir contrato del repositorio en `domain`.
2. Crear `MeService` con parsing de rangos, progreso y CRUD de citas del paciente.
3. Crear `MongoMeRepository` en `infrastructure`.
4. Crear router modular y redirigir `app/routers/me.py`.
5. Agregar test unitario del servicio.
6. Actualizar docs, roadmap y validar.

## Constraints

- mantener payloads públicos actuales;
- no tocar todavía `plans.py`;
- aceptar que la convergencia con módulos `patients` y `appointments` vendrá en slices posteriores.
