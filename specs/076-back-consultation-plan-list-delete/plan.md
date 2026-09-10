# Implementation Plan: Consultation plan link, list & delete

**Branch**: `076-back-consultation-plan-list-delete` | **Date**: 2026-09-08 | **Spec**: `specs/076-back-consultation-plan-list-delete/spec.md`

## Steps

1. `domain/entities.py`: add `plan_id: str | None = None` to `Consultation`.
2. `schemas/consultation.py`: `plan_id` on `ConsultationCloseIn` (alias `planId`) and
   `ConsultationOut`; add `patient_name: str | None = None` to `ConsultationOut` (list-only).
3. `domain/repositories.py`: add `list_for_owner(owner_id, *, status=None, patient_id=None)`
   and `delete_for_owner(owner_id, consultation_id) -> bool` to the Protocol.
4. `infrastructure/mongo_consultations_repository.py`:
   - `create_draft` doc gets `"plan_id": None`.
   - `update_for_owner` converts `plan_id` → ObjectId next to `appointment_id`/`next_appointment_id`.
   - `_to_entity` reads `plan_id` via `_stringify_maybe_oid`.
   - `list_for_owner`: `find(query).sort("updated_at", -1)`, query built from owner + optional status/patient.
   - `delete_for_owner`: `delete_one({_id, owner_id})`, return `deleted_count > 0`.
5. `application/consultations_service.py`:
   - constructor takes optional `patients_repository` (mirrors `appointments_repository`).
   - `update_close` gains `plan_id` param, merged only-if-not-None.
   - `list_consultations` → `[(consultation, patient_name)]`, names resolved once per
     distinct patient when a patients repo is present, best-effort (`except: None`).
   - `delete` → get, require `status == "draft"` else `ValueError`, then `delete_for_owner`.
6. `presentation/router.py`:
   - inject `MongoPatientsRepository` into `get_consultations_service`.
   - `_serialize(consultation, patient_name=None)` → passes `plan_id` + `patient_name`.
   - `GET ""` (list) with `status`/`patientId` Query params, before the `/{id}` GET.
   - `DELETE /{id}` → 204 via `Response(status_code=204)`.
   - `update_close` route passes `plan_id=payload.plan_id`.
7. `tests/test_consultations_service.py`: fakes get `list_for_owner`/`delete_for_owner`;
   add `_FakePatientsRepository`; +6 tests.
8. Run `test_consultations_service` then the full suite. Live `curl` smoke.

## Notes

- Route order: `GET /consultations` (`@router.get("")`) and `GET /consultations/{id}`
  don't collide (distinct paths), but list is registered first for clarity.
- `patient_name` on `ConsultationOut` is deliberately a nullable field that only the
  list path fills, rather than a separate DTO — keeps the client's single
  `ConsultationModel` parser unchanged.
