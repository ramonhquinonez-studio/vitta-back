# Feature Specification: Back Me Profile Update

**Feature Branch**: `010-back-me-profile-update`
**Created**: 2026-08-12
**Status**: Draft
**Type**: Feature

## Objective

Dar al paciente autenticado una forma de editar su propio perfil clínico básico (`name`, `age`, `sex`, `height_cm`, `allergies`). Antes solo existía `PATCH /patients/{id}`, gateado al `owner_id` del nutriólogo — inalcanzable desde la cuenta del propio paciente.

## In Scope

- `PATCH /me/profile`, reutilizando el schema `PatientUpdate` ya existente (usado por el lado pro).
- `MeRepository.update_patient_profile` + `MeService.update_profile`, siguiendo el mismo patrón de `get_patient_for_user` (la capa `me` ya toca `patients` directamente).

## Out of Scope

- Cambiar el schema o las reglas de validación de `PatientUpdate` (se reutiliza tal cual).
- Tocar `PATCH /patients/{id}` (lado pro) — sigue existiendo sin cambios, ahora como vía alterna de edición para el nutriólogo.

## Baseline Behavior

- `/me/*` solo tenía lectura de perfil (`GET /me/profile`); ninguna escritura.
- Un paciente autorregistrado (`009-back-auth-registration-and-recovery`) quedaba con `age/sex/height_cm` en `null` para siempre, sin ninguna vía propia de completarlos.

## Target Design

- `update_profile` exige patient existente (`get_patient_for_user`) y payload no vacío, igual que `update_patient` del lado pro.
- La respuesta refleja el `patients` documento actualizado completo (mismo shape que `get_patient_for_user`).

## Documentation Impact

- **Global docs to create/update**: `specs/010-back-me-profile-update/*`, `specs/SPEC_ROADMAP.md`.

## Parity Acceptance Criteria

1. Given un paciente autenticado, when hace `PATCH /me/profile` con `age/sex/height_cm/allergies`, then su `patients` queda actualizado y la respuesta lo refleja.
2. Given un payload vacío, when se llama el endpoint, then responde 400.
3. Given un usuario sin `patients` ligado, when se llama el endpoint, then responde 404.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`
