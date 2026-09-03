# Feature Specification: Distinct Tags & Allergies Endpoints

**Feature Branch**: `075-back-patient-known-tags-allergies`
**Created**: 2026-08-30
**Status**: Draft
**Type**: Enhancement

## Objective

First slice of the "Smart-Fill Roadmap" proposal (direct user request: "an autocomplete feature... for all sections where new items need to be added"). Patients' tags/allergies fields are free text with no suggestions. No viable external allergen API exists, so the fix is self-referential: expose the nutritionist's own previously-used values so the frontend can suggest them.

## In Scope

- `GET /patients/tags` — distinct `tags` values across the current nutritionist's own patients.
- `GET /patients/allergies` — distinct `allergies` values, same scoping.
- Both use the same `collection.distinct(field, filter)` primitive already used elsewhere in `mongo_patients_repository.py`'s dashboard query.

## Out of Scope

- No new collection, no caching — values are read live off `patients` on every call (small per-nutritionist datasets, no perf concern).
- No cross-nutritionist suggestions — scoped strictly to `owner_id`, same as every other patients endpoint.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro`'s `084-front-patient-tag-allergy-suggestions`.

## Acceptance Criteria

1. Given a nutritionist has patients tagged "VIP" and "Grupo A", `GET /patients/tags` returns `["Grupo A", "VIP"]` (sorted, deduped).
2. Given another nutritionist's patients use different tags, they never appear in this nutritionist's response.
3. `GET /patients/allergies` behaves identically over the `allergies` field.

## Validation

- `tests/test_patients_service.py`: 2 new tests — distinct tags/allergies scoped to owner.
- Full backend suite green (247 → 249 tests).
