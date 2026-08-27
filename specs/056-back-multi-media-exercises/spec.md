# Feature Specification: Multi-Media Exercises (Backend)

**Feature Branch**: `056-back-multi-media-exercises`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

A workout exercise carried exactly one `video_url`. TrainerStudio-style "multi-media exercises" means a coach can attach several media items per exercise — e.g. 2-3 step-by-step form photos plus a demo video — not just one clip.

## In Scope

- `WorkoutExerciseIn.video_url: Optional[str]` replaced with `media: List[WorkoutMediaIn]` (`{url, media_type}`, `media_type` constrained to `"photo"` or `"video"`).
- `POST /workout-plans/exercise-videos` renamed to `POST /workout-plans/exercise-media`, content-type gate widened from `video/*` only to `image/*` or `video/*`, `media_type` derived from the uploaded file's content-type and returned to the caller.

## Out of Scope

- `exercise_library`'s `ExerciseLibraryItem.video_url` — a separate module/collection representing one reusable reference clip, not a specific plan's authored media set. Not converted.
- No change to `max_size_bytes` (stays 150MB) — photos never approach it.
- No repository code changes — `mongo_workout_plans_repository.py` stores `days` as an opaque passthrough dict, so this is a pure schema-shape change (same precedent as `050-back-per-set-workout-authoring`).

## Baseline Behavior

`WorkoutExerciseIn.video_url` held at most one URL. `POST /workout-plans/exercise-videos` rejected any non-`video/*` content-type with `400`.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` spec `061-front-multi-media-exercises` (coach authoring) and `nutri_app` spec `058-front-multi-media-exercise-display` (patient display) both consume this.

## Acceptance Criteria

1. Given a coach uploads an image via `POST /workout-plans/exercise-media`, then it's accepted and the response reports `media_type: "photo"`.
2. Given a coach uploads a video, then it's accepted and the response reports `media_type: "video"`.
3. Given any other file type, then the endpoint rejects it with `400` ("El archivo debe ser una imagen o video.").
4. Given an exercise is saved with 2+ media items (mixed types), then `GET` on the containing plan round-trips the full list unchanged.

## Validation

- Full backend unittest suite green (no test file changes — `tests/test_workout_plans_service.py` never referenced `video_url`, matching the schema-only-change precedent from `050-back-per-set-workout-authoring`).
- Live-curl verification against the running local server: uploaded a fake image and a fake video through the renamed endpoint, confirmed `media_type` came back correctly for each; confirmed a disallowed type (`text/plain`) still rejected with `400`; created a workout plan with an exercise carrying 2 media items (one photo, one video), confirmed `GET` round-tripped the full list. Test data cleaned up afterward via a direct Motor script.
