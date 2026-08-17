# Feature Specification: Consultation History Linkage (Appointment → Plan + InBody)

**Feature Branch**: `014-back-consultation-history-linkage`
**Created**: 2026-08-16
**Status**: Draft
**Type**: Feature

## Objective

The patient-facing "Historial de consultas" screen needs, for each past appointment, the InBody scan taken at that visit and the diet plan assigned at that visit. Appointments, InBody scans (`body_compositions`), and diet plans were three independently-keyed Mongo collections with no shared reference beyond `patient_id`/`owner_id` + independent timestamps — there was no way to reconstruct "what plan/scan belongs to this consultation."

## In Scope

- `Appointment` gains an optional `body_composition_id` field, mirroring the existing `plan_id` field, threaded through the full `appointments` module stack (domain entity, repository Protocol, Mongo repository, application service, presentation router/schemas).
- `/me` module: `MeRepository.get_plan_summary(plan_id)` and `get_body_composition_by_id(id)` resolve the linked ids into summaries; `_serialize_appointment` now includes `plan_id`/`body_composition_id`.
- New `GET /me/consultations` endpoint: lists the patient's appointments (newest first), each enriched with a nested `plan` summary (`id`/`name`/`goal`) and `body_composition` summary (id/at/provider/metrics/attachment) resolved from the two linkage fields.
- One-off seed script `app/scripts/seed_ramon_consultation_history.py`: backfills 4 real past consultations for `rhq.castro@gmail.com`, each with its own `body_compositions` record and (for 3 of the 4) linked to the real assigned plan via the new `plan_id`.

## Out of Scope

- Any nutritionist-facing UI to set `body_composition_id` when logging a scan or assigning a plan — no such client exists in this repo today (nutri_app is patient-only per `CLAUDE.md`); the field is write-ready via `PATCH /appointments/{id}` (mirrors how `plan_id` already works) for whatever tool eventually needs it.
- Migrating existing `plan_id`-less appointments — only newly-created/backfilled links are affected.

## Baseline Behavior

- `GET /me/appointments` and `GET /me/appointments/{id}` never exposed `plan_id`, and `body_composition_id` did not exist on the appointment document at all.
- No endpoint could answer "what plan/scan was associated with this specific consultation."

## Target Design

- `GET /me/consultations` returns, per appointment: `id, start, end, mode, status, note, plan_id, body_composition_id, plan, body_composition` — `plan`/`body_composition` are `null` when the appointment has no linkage, resolved (not just raw ids) so the frontend needs no follow-up requests.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given an appointment with `plan_id` and `body_composition_id` set, when `GET /me/consultations` is called, then the corresponding item includes resolved `plan` and `body_composition` objects.
2. Given an appointment with neither field set, when listed, then `plan` and `body_composition` are `null` (no error).
3. Given the patient `rhq.castro@gmail.com`, when consultations are listed, then 4 real consultations are returned, newest first, 3 of them linked to the real assigned plan and all 4 linked to their own InBody-style scan.
4. `PATCH /appointments/{id}` (nutritionist-facing) accepts `body_composition_id` the same way it already accepts `plan_id`.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 31/31 green.
- Manual: ran `python -m app.scripts.seed_ramon_consultation_history`, then verified via `MeService.list_consultations` directly against dev Mongo — 4 consultations, newest-first, plan/body_composition resolved as expected.
