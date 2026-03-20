# Implementation Plan: Back Appointments Module Foundation

**Branch**: `004-back-appointments-module-foundation` | **Date**: 2026-03-20 | **Spec**: `specs/004-back-appointments-module-foundation/spec.md`

## Summary

Usar `appointments` como segundo slice backend para fijar el patrón modular con repositorio Mongo y gateway de Google Calendar.

## Steps

1. Definir entidades y contratos en `domain`.
2. Crear `AppointmentsService` con reglas de overlap y sync best-effort.
3. Crear repositorio Mongo y gateway Calendar en `infrastructure`.
4. Crear router modular y redirigir `app/routers/appointments.py`.
5. Agregar test unitario del servicio.
6. Actualizar docs, roadmap y validar.

## Constraints

- mantener payloads públicos actuales;
- no tocar todavía el router `me.py`;
- mantener Google sync como side effect no bloqueante.
