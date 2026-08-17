# Feature Specification: Appointments patient_id Filter

**Feature Branch**: `015-back-appointments-patient-filter`
**Created**: 2026-08-17
**Status**: Draft
**Type**: Feature

## Objective

`nutri_pro`'s patient-detail screen needs "this patient's appointments" (chronological history + linked plan/InBody scan per visit). `GET /appointments` had `status`/`from`/`to`/`q` filters but no way to scope to one patient short of fetching everything and filtering client-side.

## In Scope

- `patientId` (alias, snake_case `patient_id` internally) query param added to `GET /appointments`, threaded through `AppointmentsRepository.list_for_owner` (Protocol + Mongo impl), `AppointmentsService.list_appointments`, and the router.

## Out of Scope

- Any change to `POST`/`PATCH /appointments` — this is a read-filter-only addition.

## Baseline Behavior

- `GET /appointments` returned every appointment for the owner; a client wanting one patient's history had to fetch all and filter locally.

## Target Design

- `GET /appointments?patientId=<id>` returns only that patient's appointments (still respects `status`/`from`/`to`/`q` if combined).

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given an owner with appointments across multiple patients, when `GET /appointments?patientId=X` is called, then only patient X's appointments are returned.
2. Given a `patientId` with no appointments, when queried, then an empty list is returned (not an error).
3. Given no `patientId`, when queried, then behavior is unchanged from before this change.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 32/32 green (new: `test_list_appointments_filters_by_patient_id`).
- Manual: `curl "GET /appointments?patientId=6a7d79ea71f440e8e09421d6"` against the live dev server → 4 real appointments (Ramon Quinonez); `?patientId=doesnotexist` → `[]`.
