# Implementation Plan: Consultation Requirement/Distribution/Menu

**Branch**: `033-back-consultation-requirement-menu` | **Date**: 2026-08-20 | **Spec**: `specs/033-back-consultation-requirement-menu/spec.md`

## Summary

Three more section-scoped additions to the existing `consultations` module, following `evaluation`'s established shape (domain dataclass → repository merge method → service kwargs-to-dict-of-non-null → router PATCH → schema) almost verbatim for `requirement`/`distribution`, with one intentional deviation for `menu` (full-list replace instead of field merge, since a list of exchange counts has no natural partial-merge semantics).

## Steps

1. `consultations/domain/entities.py`: `RequirementInput`, `DistributionInput`, `MenuAllocationItem` frozen dataclasses; `Consultation` gains the three corresponding optional fields.
2. `consultations/domain/repositories.py`: `update_requirement_for_owner`, `update_distribution_for_owner` (same shape as `update_evaluation_for_owner`), `update_menu_for_owner(owner_id, consultation_id, allocations: list[dict])` (replace, not merge).
3. `consultations/application/consultations_service.py`: `update_requirement`, `update_distribution` (same non-null-kwargs-to-dict, empty-payload-raises-ValueError pattern as `update_evaluation`); `update_menu` (no empty-payload rejection — an empty list is a valid "cleared" state).
4. `consultations/infrastructure/mongo_consultations_repository.py`: `update_requirement_for_owner`/`update_distribution_for_owner` read-merge-write the sub-document via `dataclasses.asdict`, same as `update_evaluation_for_owner`; `update_menu_for_owner` is a direct `$set` of the whole list (no merge needed). `_to_entity` deserializes all three. `create_draft`'s initial document explicitly sets all three to `None` for consistency with the existing fields.
5. `app/schemas/consultation.py`: `ConsultationRequirementIn`, `ConsultationDistributionIn`, `MenuAllocationItemIn`/`ConsultationMenuIn`, and their `*Out` counterparts, camelCase `validation_alias` throughout matching every other module.
6. `consultations/presentation/router.py`: three new `PATCH` handlers, `_serialize` extended.
7. Tests: 6 new cases in `tests/test_consultations_service.py` against the existing fake in-memory repository (extended with the three new fake methods), mirroring the `update_evaluation`/`update_close` test style exactly.

## Constraints

- No new indexes needed — these are sub-fields of the existing `consultations` document, not new queryable dimensions.
- `app/routers/consultations.py`'s thin-wrapper re-export and `main.py`'s registration are untouched — the module was already registered by `027-back-consultations-foundation`; only its router's route set grew.
