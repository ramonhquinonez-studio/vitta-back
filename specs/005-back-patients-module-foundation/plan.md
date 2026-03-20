# Implementation Plan: Back Patients Module Foundation

**Branch**: `005-back-patients-module-foundation` | **Date**: 2026-03-20 | **Spec**: `specs/005-back-patients-module-foundation/spec.md`

## Summary

Instalar el módulo `patients` como tercer slice backend para consolidar el patrón modular sobre CRUD con paginación y ownership.

## Steps

1. Definir entidad y contrato de repositorio en `domain`.
2. Crear `PatientsService` en `application`.
3. Crear `MongoPatientsRepository` en `infrastructure`.
4. Crear router modular y redirigir `app/routers/patients.py`.
5. Agregar test unitario del servicio.
6. Actualizar docs, roadmap y validar.

## Constraints

- mantener payloads públicos actuales;
- no tocar todavía `me.py`;
- seguir reutilizando `app/schemas/patients.py` y `pagination.py` por compatibilidad.
