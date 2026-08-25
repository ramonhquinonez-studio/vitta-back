# Implementation Plan: Custom Check-In Forms

**Branch**: `044-back-checkin-forms` | **Date**: 2026-08-25 | **Spec**: `specs/044-back-checkin-forms/spec.md`

## Summary

A new `checkin` module for nutritionist-owned template CRUD (mirroring `equivalencies`'s module shape), plus small extensions to the existing `me` module (patient-side read/write, matching `messages`/`measurements` precedent) and `patients` module (nutritionist-side read, matching `043-back-progress-photos`'s `list_measurements`).

## Steps

1. `checkin/domain/entities.py`: `FormField`, `FormTemplate`, `FormAnswer`, `FormResponse` dataclasses.
2. `checkin/domain/repositories.py`: `CheckinRepository` Protocol (`create_template`, `list_templates`, `get_template`, `update_template`, `archive_template`).
3. `checkin/infrastructure/mongo_checkin_repository.py`: standard owner-scoped CRUD against `checkin_templates`.
4. `checkin/application/checkin_service.py`: template CRUD + payload validation (title required, ≥1 field, valid field type, every field has a label, choice fields have ≥1 option).
5. `app/schemas/checkin.py`: `FormFieldIn`/`FormTemplateCreate`/`FormTemplateOut`, `FormAnswerIn`/`FormResponseCreate`/`FormResponseOut`.
6. `checkin/presentation/router.py` (`prefix="/checkin"`, nutritionist-only): `POST/GET /templates`, `GET/PATCH/DELETE /templates/{id}` (`DELETE` archives, doesn't hard-delete).
7. `app/routers/checkin.py` wrapper + `main.py` wiring.
8. `me/domain/repositories.py` + `infrastructure/mongo_me_repository.py`: `list_checkin_templates`, `get_checkin_template`, `create_checkin_response`, `list_checkin_responses`, reading/writing the same `checkin_templates`/`checkin_responses` collections the `checkin` module owns.
9. `me/application/me_service.py`: `list_checkin_templates`, `submit_checkin_response` (resolves `owner_id` from the patient's own linked record, validates the template belongs to that owner, validates required fields via `_validate_checkin_answers`), `list_checkin_responses`.
10. `me/presentation/router.py`: `GET /checkin-templates`, `POST/GET /checkin-responses`.
11. `patients/domain/repositories.py` + `infrastructure`/`application`/`presentation`: `list_checkin_responses`, same ownership-check-then-query shape as `list_measurements`.
12. Tests: `tests/test_checkin_service.py` (fake repository), extensions to `tests/test_me_service.py` and `tests/test_patients_service.py`.

## Constraints

- Answers are always `{field_id, values: list[str]}` on the wire, regardless of field type — a deliberate simplification to avoid a polymorphic value type in either Flutter app's domain layer.
- Archiving a template never deletes it or its historical responses — `DELETE /checkin/templates/{id}` only flips `archived=true`.
