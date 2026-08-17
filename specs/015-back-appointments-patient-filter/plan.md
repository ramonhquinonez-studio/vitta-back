# Implementation Plan: Appointments patient_id Filter

**Branch**: `015-back-appointments-patient-filter` | **Date**: 2026-08-17 | **Spec**: `specs/015-back-appointments-patient-filter/spec.md`

## Summary

One-parameter addition mirroring the existing `status` filter's shape end-to-end.

## Steps

1. `appointments/domain/repositories.py`: add `patient_id: str | None = None` to `AppointmentsRepository.list_for_owner`.
2. `appointments/infrastructure/mongo_appointments_repository.py`: add `patient_id` to the aggregation `$match` (converted via `_oid_maybe`).
3. `appointments/application/appointments_service.py`: pass `patient_id` through `list_appointments`.
4. `appointments/presentation/router.py`: `patient_id: str | None = Query(None, alias="patientId")` on `list_appointments`.
5. `tests/test_appointments_service.py`: `_FakeAppointmentsRepository.list_for_owner` gains `patient_id=None` kwarg; new test `test_list_appointments_filters_by_patient_id`.

## Constraints

- No schema/response shape change — `AppointmentOut` already includes `patient_id`, so no new fields needed, just a new filter input.
