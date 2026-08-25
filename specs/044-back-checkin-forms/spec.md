# Feature Specification: Custom Check-In Forms

**Feature Branch**: `044-back-checkin-forms`
**Created**: 2026-08-25
**Status**: Draft
**Type**: Feature

## Objective

Phase 1d of the TrainerStudio gap analysis, the last of the four Phase 1 engagement slices (following `042-back-patient-nutritionist-chat` and `043-back-progress-photos`). A nutritionist can author a check-in form (an ordered list of typed fields — text/number/single-choice/multi-choice/scale), and a patient can fill one in and submit a response, repeatedly. This was fully greenfield — the existing `consultations` module's 6-step wizard is a fixed schema baked into hardcoded dataclasses, architecturally the opposite of a dynamic, nutritionist-authored field list.

## In Scope

- New `checkin` module: `FormField` (`id, type, label, required, options, scale_min, scale_max`), `FormTemplate` (`id, owner_id, title, description, fields, archived, created_at, updated_at`), `FormAnswer` (`field_id, values: list[str]`), `FormResponse` (`id, owner_id, patient_id, template_id, appointment_id, answers, submitted_at`).
- Nutritionist-owned template CRUD under `/checkin/templates`: create, list (excludes archived by default), get by id, full-replace update, and a soft-delete (`archived=true`, not a hard delete — a hard delete would orphan historical responses' field labels/types).
- Patient-side, extending the `me` module (matching the established precedent — `me` reads/writes shared collections directly rather than delegating to a sibling module's service, same as `messages`/`measurements`): `GET /me/checkin-templates` (the patient's own nutritionist's active templates — always fillable, no separate "assignment" step, same visibility model as `content_library`), `POST /me/checkin-responses` (validates the template belongs to the patient's own nutritionist and that every required field has a non-empty answer), `GET /me/checkin-responses`.
- Nutritionist-side response reading, extending the `patients` router (same pattern as `043-back-progress-photos`'s `list_measurements`): `GET /patients/{patient_id}/checkin-responses`.
- Every answer is `{field_id, values: list[str]}` regardless of field type — text/number/scale each store a single-element list, single_choice one element, multi_choice N elements. Deliberate v1 simplification: avoids a polymorphic "any" value type on the wire, at the cost of no numeric aggregation of check-in answers in this pass.

## Out of Scope

- No `appointment_id` requirement — nullable throughout, mirroring `Consultation.appointment_id`'s existing shape, since a check-in can be a standalone/recurring thing (e.g. weekly weigh-in-style) as easily as something tied to a specific visit.
- No template "assignment" to specific patients — every one of a nutritionist's active templates is visible to all of their patients.
- No numeric aggregation or trend-charting of check-in answers — a natural future extension, not built here.
- No `TestClient`/router-level integration tests — matches this repo's established service-level-only test convention; live curl verification substitutes for that layer.

## Baseline Behavior

No dynamic, nutritionist-authorable form concept existed. The only "form" in the product was the fixed 6-step consultation wizard (Inicio/Evaluación/Requerimiento/Distribución/Menú/Cierre), which is not patient-facing and not customizable per nutritionist.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro` spec `042-front-checkin-forms` (template authoring) and `nutri_app` spec `050-front-checkin-forms` (fill-in UI).

## Acceptance Criteria

1. Given a nutritionist creates a template with one field of each type, then `GET /checkin/templates` and `GET /checkin/templates/{id}` return it with all fields intact.
2. Given that template is active, when the patient calls `GET /me/checkin-templates`, then it appears.
3. Given the patient submits a response missing a required field, then `POST /me/checkin-responses` is refused with `400`.
4. Given the patient submits a complete response, then it appears both in their own `GET /me/checkin-responses` and the nutritionist's `GET /patients/{patient_id}/checkin-responses`.
5. Given a nutritionist who doesn't own that patient, when calling `GET /patients/{patient_id}/checkin-responses`, then it's refused with `404`.
6. Given the nutritionist archives the template, then it disappears from the patient's active `GET /me/checkin-templates` list, but `GET /checkin/templates/{id}` still resolves it (so old responses can still be displayed against their original field labels).

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 179/179 green (8 new `test_checkin_service.py` cases, 6 new `test_me_service.py` cases, 2 new `test_patients_service.py` cases).
- Live verification against the running backend: created a template with all five field types, confirmed required-field validation rejects an incomplete submission (`400`), confirmed a complete submission round-trips through both the patient's and the nutritionist's read endpoints, confirmed a second unrelated nutritionist gets `404`, confirmed archiving removes the template from the patient's active list while it remains fetchable by id for resolving old responses. Test accounts/data cleaned up after.
