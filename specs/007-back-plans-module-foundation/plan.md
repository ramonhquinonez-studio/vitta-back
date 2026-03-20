# Implementation Plan: Back Plans Module Foundation

**Branch**: `007-back-plans-module-foundation` | **Date**: 2026-03-20 | **Spec**: `specs/007-back-plans-module-foundation/spec.md`

## Summary

Instalar el módulo `plans` como último slice grande de routers legacy para dejar el backend casi por completo migrado a `app/modules/`.

## Steps

1. Definir contrato del repositorio en `domain`.
2. Crear `PlansService` con CRUD, grocery list y assign.
3. Crear `MongoPlansRepository` en `infrastructure`.
4. Crear router modular y redirigir `app/routers/plans.py`.
5. Agregar test unitario del servicio.
6. Actualizar docs, roadmap y validar.

## Constraints

- mantener payloads públicos actuales;
- no tocar todavía `me/plan/active`;
- mantener `app/schemas/plan.py` como contrato HTTP actual.
