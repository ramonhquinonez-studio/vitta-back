# Feature Specification: Consultation plan link, list & delete

**Feature Branch**: `076-back-consultation-plan-list-delete`
**Created**: 2026-09-08
**Status**: Done
**Type**: Enhancement

## Objective

Backend half of `nutri_pro`'s `106-front-consultation-workflow-improvements`. The
consultation wizard (`027-back-consultations-foundation`) needs three things it
can't currently do: record the plan assigned during the closing step, list a
nutritionist's open drafts (so an interrupted session is findable), and discard a
draft that was started and abandoned.

## In Scope

- **`Consultation.plan_id`** (`str | None`): new field on the entity, `ConsultationOut`,
  and `ConsultationCloseIn` (alias `planId`). `update_close` merges it like
  `private_notes`/`next_appointment_id` (only-if-provided). Mongo repo converts it to
  an ObjectId on write alongside the other id fields. The client assigns the plan to
  the patient itself (existing `POST /plans/{id}/assign`); this only persists the
  choice onto the consultation.
- **`GET /consultations`** — lists the caller's consultations, newest-`updated_at`
  first, with optional `?status=` and `?patientId=` query filters. Response is
  `list[ConsultationOut]`; on this path only, each row's `patient_name` is resolved
  (one lookup per distinct patient, via an optionally-injected patients repository —
  same pattern as the existing optional appointments repository) so list UIs need no
  fan-out. `patient_name` stays `None` on every single-consultation response.
- **`DELETE /consultations/{id}`** — 204 on success. Service rejects a non-draft
  consultation with `ValueError` → 400 ("Only a draft consultation can be discarded"),
  and a missing one with `LookupError` → 404. A completed consultation is a frozen
  historical record and cannot be deleted.

## Out of Scope

- No cascade: deleting a draft doesn't touch any appointment it linked or plan it
  assigned (those are independent records with their own lifecycle).
- No pagination on `GET /consultations` — per-nutritionist draft counts are tiny.
- Plan *authoring* stays entirely in the `plans` module; consultations only store the id.

## Documentation Impact

- **Global docs**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro`'s `106-front-consultation-workflow-improvements`.

## Acceptance Criteria

1. `PATCH /consultations/{id}/close` with `{"planId": "<id>"}` persists it; it comes
   back as `plan_id` on that and every later fetch of the consultation.
2. `GET /consultations?status=draft` returns only the caller's drafts, each carrying
   `patient_name`; another nutritionist's consultations never appear.
3. `DELETE /consultations/{id}` on a draft → 204, and a subsequent `GET` → 404.
4. `DELETE /consultations/{id}` on a completed consultation → 400, record untouched.

## Validation

- `tests/test_consultations_service.py`: +6 tests (plan_id in close; list filters by
  status; list attaches patient name; list without a patients repo → no names; delete
  removes a draft; delete rejects a completed one; delete raises when missing).
- Full backend suite green (255 tests).
- Live `curl` end-to-end: register → patient → start → `GET ?status=draft` (shows
  `patient_name`) → close with `planId` (persists) → DELETE draft (204 → GET 404) →
  complete + DELETE (400).
