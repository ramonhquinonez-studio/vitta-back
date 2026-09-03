# Feature Specification: Real Supplements/Brands Library + Per-Patient Assignment (Backend)

**Feature Branch**: `069-back-recommendations-platform-and-assignment`
**Created**: 2026-08-28
**Status**: Draft
**Type**: Feature

## Objective

`recommendations` ("Suplementos y marcas") was a single nutritionist-authored list — every patient of a given nutritionist saw the exact same full list via `GET /me/recommendations`, with no platform-curated content and no per-patient targeting. This adds three things, mirroring patterns already proven elsewhere in this app:

1. **Real official data**: a platform tier (`owner_id: null`), synced from two NIH-family sources — MedlinePlus (narrative Spanish descriptions, same source and parsing pipeline as `060-back-medlineplus-content-library`) for supplements, and the Dietary Supplement Label Database (DSLD, `api.ods.od.nih.gov`) for brands. The originally-considered `ods.od.nih.gov` fact-sheet site is fully Cloudflare-blocked (confirmed via direct `curl` returning a JS challenge on every path) and was abandoned in favor of these two working, unblocked, keyless NIH subdomains.
2. **Real per-patient assignment**: a new `recommendation_assignments` collection lets a nutritionist assign a specific recommendation to specific patients, and unassign it later.
3. **Curated real brand names**: every synced brand is verified to exist as an exact `brandName` match in DSLD's live label registry before being included, satisfying "brands must be real product brands."

## In Scope

- `Recommendation.owner_id` becomes optional (`null` = platform), mirroring `content_library`/`exercise_library`'s existing platform-tier pattern exactly.
- `GET /recommendations/platform` — platform-curated list, same shape as `GET /content/articles/platform`.
- New `recommendation_assignments` collection: `{owner_id, recommendation_id, patient_id, assigned_at}`. Unlike `plan_assignments` (insert-only, no unassign — "current" is derived by most-recent), this collection supports real **unassign** (`DELETE`) and **multi-patient assign in one call** — a deliberate deviation, since a supplement recommendation is a lighter, more-frequently-toggled thing than a nutrition/workout plan.
- `POST /recommendations/{id}/assign` (body `{"patient_ids": [...]}`), `DELETE /recommendations/{id}/assign/{patient_id}`, `GET /recommendations/{id}/assignments`.
- `GET /me/recommendations` **behavior change**: now returns only recommendations actually assigned to the calling patient (via `recommendation_assignments`), instead of every recommendation the nutritionist has ever authored. This is the intended, necessary consequence of adding real assignment.
- `owner_id` added to `RecommendationOut`, so `nutri_pro` can distinguish platform vs. owned items (mirroring `ArticleOut.owner_id`).
- New `app/scripts/sync_recommendations_library.py`: 14 curated supplement terms via MedlinePlus free-text search, 10 curated brand names via DSLD, idempotent upsert by stable `_id` slug.
- Assign-from-mine only (not assign-from-platform-tab directly): a nutritionist copies a platform recommendation into their own library first (`POST /recommendations`, same "Guardar en mi biblioteca" pattern as articles/exercises), then assigns from "Mis recomendaciones" — keeps one consistent mental model across all "platform + mine" library features.

## Out of Scope

- No frontend changes in this spec (covered by `nutri_pro` spec `078-front-recommendations-platform-and-assignment` and `nutri_app` spec `065-front-recommendations-assigned-only`).
- No direct assign-from-platform-tab flow.
- No automatic/scheduled re-sync of the platform catalog — run `sync_recommendations_library.py` manually, matching every other sync script in this codebase.

## Baseline Behavior

`recommendations` had no platform tier and no per-patient filtering: `GET /me/recommendations` returned every recommendation the nutritionist had ever authored, filtered only by `owner_id`.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` (new platform tab + assignment UI, spec `078-front-recommendations-platform-and-assignment`) and `nutri_app` (behavior-change documentation only, spec `065-front-recommendations-assigned-only` — no code change expected).

## Acceptance Criteria

1. Given the sync script runs, then it upserts platform (`owner_id: null`) `recommendations` documents — one per curated supplement (Spanish MedlinePlus description + attribution) and one per curated brand (DSLD-verified name + aggregated product categories + attribution).
2. Given a nutritionist calls `GET /recommendations/platform`, then only `owner_id: null` documents are returned.
3. Given a nutritionist copies a platform recommendation (`POST /recommendations`) and assigns it to one or more patients (`POST /recommendations/{id}/assign`), then those patients' `GET /me/recommendations` includes it and other patients' does not.
4. Given a nutritionist unassigns a patient (`DELETE /recommendations/{id}/assign/{patient_id}`), then that patient's `GET /me/recommendations` no longer includes it.
5. Given a nutritionist calls `GET /recommendations/{id}/assignments`, then it returns exactly the currently-assigned patient ids.
6. Given a nutritionist tries to assign a recommendation they don't own (including a platform item, not yet copied), then the request 404s.

## Validation

- Full backend unittest suite green (236/236 — 12 new tests: 5 in `test_recommendations_service.py` for platform list + assign/unassign/ownership checks, 2 in `test_me_service.py` for the assigned-only behavior and patient-id threading).
- Live sync run against the real MedlinePlus and DSLD APIs: 24/24 curated items synced (14 supplements, 10 brands) after fixing two live-verified issues — "NOW Foods" swapped for "Jarrow Formulas" (DSLD's search treats "NOW" as an unsearchable stopword-like token, confirmed via direct query), and the outgoing DSLD query for brands with an apostrophe (`Nature's Bounty`) has the apostrophe stripped before searching while the exact-match check still requires the real (apostrophe-included) `brandName` back — confirmed live this recovers the correct brand as the top result.
- Live end-to-end round-trip against the running local server with throwaway QA accounts (`qa-nutri-069b@example.com` / QA patient via invite code): platform list → copy into "mine" → assign → `GET /me/recommendations` shows it for the assigned patient only → `GET /recommendations/{id}/assignments` confirms the patient id → unassign → `GET /me/recommendations` empty again. QA accounts, patient record, invite code, and the copied recommendation were deleted afterward; the 24 real synced platform recommendations were kept.
