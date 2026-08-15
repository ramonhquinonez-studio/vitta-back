# Implementation Plan: Back Me Profile Update

**Branch**: `010-back-me-profile-update` | **Date**: 2026-08-12 | **Spec**: `specs/010-back-me-profile-update/spec.md`

## Summary

Agregar la escritura que le faltaba a `me` module para el perfil del propio paciente, reusando `PatientUpdate` y el patrón ya establecido de `get_patient_for_user`.

## Steps

1. `MeRepository` (domain): `update_patient_profile(patient_id, payload)`.
2. `MongoMeRepository`: implementación, mismo shape de salida que `get_patient_for_user`.
3. `MeService.update_profile(user_id, payload)`: valida payload no vacío + patient existente.
4. Router: `PATCH /me/profile` con `PatientUpdate` (reuso de `app/schemas/patients.py`).
5. `tests/test_me_service.py`: casos de éxito, payload vacío, usuario sin patient.

## Constraints

- Sin nuevo schema: `PatientUpdate` ya tenía exactamente los campos necesarios.
- No se toca `patients` router/service (lado pro).
