# Implementation Plan: Real Supplements/Brands Library + Per-Patient Assignment (Backend)

**Branch**: `069-back-recommendations-platform-and-assignment` | **Date**: 2026-08-28 | **Spec**: `specs/069-back-recommendations-platform-and-assignment/spec.md`

## Summary

Extend the existing `recommendations` module with a platform tier and a new assignment collection, following `content_library`'s platform pattern and deliberately deviating from `plan_assignments`' insert-only shape. Add a new standalone sync script for real data.

## Steps

1. `app/modules/recommendations/domain/entities.py`: `Recommendation.owner_id: str` → `str | None`.
2. `domain/repositories.py`: add `list_platform_recommendations(*, kind=None)`, `assign_to_patients(owner_id, recommendation_id, patient_ids) -> int`, `unassign_from_patient(owner_id, recommendation_id, patient_id) -> bool`, `list_assigned_patient_ids(owner_id, recommendation_id) -> list[str]` to the `RecommendationsRepository` Protocol.
3. `infrastructure/mongo_recommendations_repository.py`:
   - `list_platform_recommendations` queries `{"owner_id": None}` (+ optional kind).
   - `assign_to_patients` verifies the recommendation is owned by `owner_id` first (returns 0 if not — platform items and other nutritionists' items can't be assigned directly), then upserts one `recommendation_assignments` doc per patient (`update_one` with `$setOnInsert`, `upsert=True`), returning the count processed.
   - `unassign_from_patient` / `list_assigned_patient_ids` operate directly on `recommendation_assignments`.
   - `_to_entity` made null-safe for `owner_id` (`str(doc["owner_id"]) if doc.get("owner_id") is not None else None`).
4. `application/recommendations_service.py`: thin passthroughs; `assign_to_patients` raises `ValueError` for an empty `patient_ids` list and `LookupError` when the repository reports 0 (not owned); `unassign_from_patient` raises `LookupError` when nothing was removed.
5. `presentation/router.py`: `GET /recommendations/platform`, `POST /recommendations/{id}/assign`, `DELETE /recommendations/{id}/assign/{patient_id}`, `GET /recommendations/{id}/assignments`; `_serialize()` and `RecommendationOut` gain `owner_id`.
6. `app/modules/me/`: `MeRepository.list_recommendations` Protocol signature gains a required `patient_id` param (needed to join through `recommendation_assignments` — `owner_id` alone is no longer enough to scope the result). `MeService.list_recommendations` passes `patient["id"]` through. `MongoMeRepository.list_recommendations` looks up the patient's assigned `recommendation_id`s first, returns `[]` immediately if none, otherwise queries `recommendations` with `_id: {"$in": assigned_ids}` (+ optional kind) — replacing the old owner-scoped-only query.
7. New `app/scripts/sync_recommendations_library.py` — reuses `sync_medlineplus_content_library.py`'s `_SummaryParser`/`_strip_tags` pattern (small self-contained copy, matching this codebase's per-script-standalone precedent):
   - `_SUPPLEMENTS: dict[str, str]` (14 Spanish display names → MedlinePlus free-text search terms). For each: `GET wsearch.nlm.nih.gov/ws/query?db=healthTopicsSpanish&term=<term>&retmax=1`, take the top document, parse its inline `FullSummary` → `description` (+ "Fuente: MedlinePlus.gov"), `benefits` from bullet items, `kind="supplement"`, `owner_id=None`, stable `_id: recommendation-supplement-<slug>`.
   - `_BRANDS: list[str]` (10 real brand names). For each: `GET api.ods.od.nih.gov/dsld/v9/search-filter?q=<brand>&size=25`, filter hits to exact (case-insensitive) `brandName` match, aggregate the top `productType.langualCodeDescription` values into `category`/`subtitle`, `description` cites "Fuente: NIH Dietary Supplement Label Database (dsld.od.nih.gov)", `kind="brand"`, `owner_id=None`, stable `_id: recommendation-brand-<slug>`.
   - Idempotent upsert by `_id` (`update_one({"_id": ...}, {"$set": doc}, upsert=True)`), matching every other sync script's shape. `sync(*, limit=None)` / `main()` bracket via `connect_to_mongo`/`close_mongo_connection`.
8. Tests: `tests/test_recommendations_service.py` — extend the fake repository with `list_platform_recommendations`/`assign_to_patients`/`unassign_from_patient`/`list_assigned_patient_ids`, add tests for platform listing, assign→list→unassign, assign requiring a non-empty patient list, assign rejecting a recommendation not owned, unassign rejecting a nonexistent assignment. `tests/test_me_service.py` — update `_FakeMeRepository.list_recommendations` to the new signature, add a test asserting the calling patient's id is threaded through.
9. Live verification: run the sync script for real, fix any live-discovered gaps (see spec's Validation section for the two found), re-run to confirm 24/24; exercise the full assign/unassign/read round-trip against the running local server with throwaway QA accounts, clean up QA-only data afterward while keeping the synced platform content.

## Constraints

- `list_recommendations`'s Protocol signature change (adding `patient_id`) is a deliberate, necessary deviation from the plan's original assumption that `me_service.list_recommendations` would need no change — assignment-based filtering genuinely requires the calling patient's id, which the old owner-only signature didn't carry.
- `assign_to_patients` deliberately scopes to recommendations the nutritionist owns (not platform items) — assignment always goes through a copied "mine" item, keeping one consistent copy-then-act mental model across the app's platform+mine features.
