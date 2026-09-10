# Tasks: Consultation plan link, list & delete

- [x] T1 — `Consultation.plan_id` on entity.
- [x] T2 — `plan_id` on `ConsultationCloseIn`/`ConsultationOut`; `patient_name` on `ConsultationOut`.
- [x] T3 — `list_for_owner` + `delete_for_owner` on the repository Protocol.
- [x] T4 — Mongo repo: plan_id in create/update/entity; `list_for_owner`; `delete_for_owner`.
- [x] T5 — Service: optional `patients_repository`; `update_close` plan_id; `list_consultations`; `delete` (draft-only).
- [x] T6 — Router: patients repo injection; `_serialize` plan_id + patient_name; `GET /consultations`; `DELETE /consultations/{id}`; close passes plan_id.
- [x] T7 — `tests/test_consultations_service.py`: +6 tests, fakes updated.
- [x] T8 — `test_consultations_service` green; full suite green (255).
- [x] T9 — Live `curl` smoke (list/close-plan/delete-draft/delete-completed).
- [x] T10 — Add `076-back-consultation-plan-list-delete` to `specs/SPEC_ROADMAP.md`.
