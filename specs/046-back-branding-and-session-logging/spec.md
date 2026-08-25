# Feature Specification: Per-Tenant Branding Upload + Exercise Library + Logged Session Details

**Feature Branch**: `046-back-branding-and-session-logging`
**Created**: 2026-08-24
**Status**: Draft
**Type**: Feature

## Objective

Closes two gaps flagged against the original TrainerStudio comparison (published gap-analysis artifact, "Vitta vs. TrainerStudio"): the real Phase 2 (dynamic per-tenant branding — never built; a prior session mislabeled the Phase 3 training-domain work as "Phase 2") and two under-built pieces of Phase 3 (training domain): no reusable exercise library, and workout completion was a bare boolean with no logged performance. Research found the branding fields (`logo_url`/`brand_color`/`practice_name`) already existed end-to-end on `NutritionistProfile` from earlier onboarding work — only a logo *upload* endpoint was missing, plus one place `me`'s read path silently dropped them.

## In Scope

- `nutritionist_profile` module: `POST /nutritionist_profile/me/logo` (multipart, mirrors `patients`' body-composition photo upload — `save_upload(file, subfolder=f"nutritionist_profile/{owner_id}")`), then updates `logo_url` via the existing `update_my_profile`.
- `me` module: `mongo_me_repository.py`'s `get_nutritionist_profile` now includes `practice_name`/`logo_url`/`brand_color` in its returned dict (previously silently dropped despite the underlying profile document already having them).
- `me`/`patients` modules: `workout_logs` documents gain optional `sets_completed, reps_completed, weight_kg, rpe, comment`. `POST /me/workout-logs/toggle` accepts an optional `details` object — stored on create, discarded on delete (un-toggle is a full clear, not a partial edit). Both `list_workout_logs` read paths (patient's own `GET /me/workout-logs` and the nutritionist's `GET /patients/{id}/workout-logs`) return these fields.
- New `exercise_library` module (mirrors `equivalencies`' nutritionist-authored-custom-item shape exactly): `ExerciseLibraryItem{id, owner_id, name, default_sets, default_reps, default_weight_kg, default_duration_seconds, default_rest_seconds, video_url, notes}`. `POST/GET /exercise-library`, `DELETE /exercise-library/{id}`, nutritionist-only.

## Out of Scope

- No licensed exercise content/video database — the library is nutritionist-authored-and-reused only, same honesty-of-scope as `equivalencies`' custom foods; there is no content-licensing relationship to build against.
- No session photos on a logged workout entry — flagged as a future increment, not built here (lower value-per-effort than the numeric/text fields, consistent with every other slice this session drawing a similar scope line).
- No native per-tenant App Store/Play Store listings — permanently out of scope per the gap-analysis artifact's own flag (infra business, not a coaching-product feature); in-app branding is the correct scope.
- No re-theme of `nutri_pro` (the nutritionist's own app) — branding is patient-facing only, per design decision below.

## Design Decisions

1. **Branding is patient-facing only.** TrainerStudio's actual claim is "every trainer's client sees the trainer's own logo/color" — `nutri_pro` doesn't need to reflect its own user's brand back at them.
2. **`toggle_workout_log`'s `details` is create-only, not a partial-update mechanism.** Re-toggling an already-completed exercise deletes the row (discarding any details) before a subsequent toggle can recreate it with new details — an explicit simplification consistent with the existing idempotent complete/incomplete switch design from `045-back-workout-plans`, not a regression from it.

## Baseline Behavior

`NutritionistProfile.logo_url`/`brand_color`/`practice_name` already existed as full fields (entity → Mongo → service `_serialize` → `NutritionistProfileOut`/`Update` schemas → `PATCH /nutritionist_profile/me`) from earlier onboarding work, but `logo_url` was settable only if the caller already had a URL (no upload path), and `me`'s read side dropped all three fields before they ever reached a patient. `workout_logs` (from `045-back-workout-plans`) had no fields beyond the identifying key + `completed_at`.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro` spec `044-front-branding-and-exercise-library` (branding edit UI, exercise-library authoring/picker) and `nutri_app` spec `052-front-branding-and-session-logging` (dynamic accent theming, session-logging UI).

## Acceptance Criteria

1. Given a nutritionist uploads a logo via `POST /nutritionist_profile/me/logo`, then `logo_url` is returned, publicly fetchable (unauthenticated `/uploads/...` static mount), and a linked patient's `GET /me/nutritionist_profile` reflects it.
2. Given a nutritionist saves an item to `POST /exercise-library`, then it appears in their own `GET /exercise-library` and not in another nutritionist's.
3. Given a patient toggles a workout log with a `details` object attached, then both their own `GET /me/workout-logs` and their nutritionist's `GET /patients/{id}/workout-logs` show the same logged numbers.
4. Given the same exercise is toggled again (un-toggle), then the log row — details included — is fully removed, not partially cleared.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 203/203 green (5 new `test_exercise_library_service.py` cases, 1 new `test_me_service.py` case).
- Live verification against the running backend: logo uploaded and confirmed fetchable (`200 image/png`) and visible on a linked patient's profile read; exercise-library item created/listed/deleted; workout log toggled with `details` and confirmed identical on both the patient's and nutritionist's read paths. Throwaway test accounts/data cleaned up after.
