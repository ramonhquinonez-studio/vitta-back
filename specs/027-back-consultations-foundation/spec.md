# Feature Specification: Consultation Session Foundation

**Feature Branch**: `027-back-consultations-foundation`
**Created**: 2026-08-19
**Status**: Draft
**Type**: Feature

## Objective

Give the nutritionist app a stateful, resumable "consultation session" entity — the backend half of Phase 1 of the "Consultation as one continuous session" redesign. A nutritionist can start a consultation for a patient, fill in an evaluation section, add private close notes, optionally link a next appointment, and complete it (freezing the record) — closing the laptop mid-session and reopening it later resumes exactly where they left off, since every section autosaves independently.

## In Scope

- New `consultations` module (`domain/application/infrastructure/presentation`, mirroring `equivalencies`' shape): `Consultation` entity (id, owner_id, patient_id, appointment_id?, status, current_step, visit_type?, evaluation?, private_notes?, next_appointment_id?, completed_at?) and `EvaluationSnapshot` (weight_kg, height_cm, body_fat_pct, waist_cm, hip_cm, arm_cm, notes — all optional).
- `POST /consultations/start` — resumes the patient's existing open (`status="draft"`) consultation if one exists, otherwise creates a new one. If an `appointment_id` is supplied and the resumed draft doesn't have one yet, it's backfilled. The client never has to know which case it is.
- `GET /consultations/{id}`, `PATCH /consultations/{id}` (top-level: `visit_type`, `current_step`), `PATCH /consultations/{id}/evaluation` (section-scoped, merges only the provided fields into whatever's already saved), `PATCH /consultations/{id}/close` (`private_notes`, `next_appointment_id`), `POST /consultations/{id}/complete` (freezes: `status="completed"`, `completed_at` set; rejects an already-completed consultation with 400).
- `app/db/init_indexes.py`: `(owner_id, patient_id, status)` and `(owner_id, created_at)` indexes on `consultations`, matching the query shapes `find_open_draft` and typical listing would use.

## Out of Scope

- Requirement/macro calculation, per-meal distribution, menu authoring — Phases 2-3 of the redesign, once this foundation and the nutritionist-facing wizard shell are real.
- Branded PDF generation and email/WhatsApp sending — a separate scoping pass once the earlier phases are in use (see the published proposal's Phase 4).
- InBody OCR/autofill — explicitly deferred; manual entry (already the only mechanism here) remains the permanent fallback regardless.
- A `GET /consultations` list endpoint — not needed until a consultation-history UI is built on top of this foundation; `list_consultations` on the `me` module (patient-facing, spec `014-back-consultation-history-linkage`) already covers read-only history display and is unrelated to this stateful entity.

## Baseline Behavior

- No stateful "consultation" concept existed. `014-back-consultation-history-linkage`'s `GET /me/consultations` is a read-only join of appointment + plan + body_composition for patient-side history display — nothing writes to it beyond the existing `PATCH /appointments/{id}`, and it has no lifecycle of its own. This slice is a categorically different, new entity: a stateful, resumable session.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`
- **Cross-repo impact**: `nutri_pro` gains the consultation wizard shell that consumes this (its own spec).

## Acceptance Criteria

1. Given a nutritionist starts a consultation for a patient who has no open draft, then a new `draft` consultation is created at `current_step=1`.
2. Given a nutritionist starts a consultation for a patient who already has an open draft, then that same draft is returned (not a new one) — and if an `appointment_id` is passed and the draft didn't have one, it gets backfilled.
3. Given a nutritionist saves part of the evaluation section, then later saves a different part, then both parts are present on read — a partial save never overwrites fields it didn't touch.
4. Given a nutritionist completes a consultation, then its status becomes `completed`, `completed_at` is set, and attempting to complete it again fails with a 400.
5. Given a nutritionist starts a new consultation for a patient whose most recent consultation was already completed, then a brand-new draft is created (completed consultations are never resumed).

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 96/96 green (10 new tests in `test_consultations_service.py`; both router guardrail/smoke tests extended for the new module).
- Manual: `curl` end-to-end against the live local backend — registered a throwaway nutritionist, created a throwaway patient, started a consultation, confirmed resume-same-draft and appointment-id-backfill behavior, PATCHed the evaluation section twice and confirmed the merge-only-provided-fields behavior exactly, PATCHed close notes, completed the consultation, confirmed double-complete returns 400, and confirmed starting again afterward creates a fresh draft rather than resuming the frozen one.
