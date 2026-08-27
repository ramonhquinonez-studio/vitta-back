# Feature Specification: Exercise Video Upload

**Feature Branch**: `047-back-exercise-video-upload`
**Created**: 2026-08-25
**Status**: Draft
**Type**: Feature

## Objective

A workout exercise's `video_url` (on both `workout_plans` and `exercise_library`, from `045-back-workout-plans`/`046-back-branding-and-session-logging`) is a plain URL string a nutritionist pastes a link into. The user asked whether they can record a training video directly in `nutri_pro` instead — they could not. This adds an upload endpoint returning a URL that fits the exact same field, so recording/picking a device video becomes an alternative way to fill it, not a schema change.

## In Scope

- `workout_plans` module: `POST /workout-plans/exercise-videos` (nutritionist-only, multipart), stores under `workout_plans/{owner_id}/videos`, returns `{video_url, content_type}`.
- `app/core/storage.py`'s shared `save_upload` helper gains an optional `max_size_bytes` guard (raises `ValueError` when exceeded) and video content-type→extension mappings (`video/mp4`, `video/quicktime`, `video/webm`) — this is the first upload surface in the codebase handling files large enough to need a size cap.
- Content-type validation: the endpoint rejects a non-`video/*` upload with `400` before ever calling `save_upload`.

## Out of Scope

- No change to `WorkoutExerciseIn`/`WorkoutExerciseOut`/`ExerciseLibraryItemCreate`/`Out` schemas — `video_url` already exists and accepts any string, pasted or uploaded.
- No video transcoding, thumbnailing, or duration inspection — the raw uploaded file is stored as-is.
- No streaming/chunked upload — matches every other upload in this codebase (logo, body-composition photos, progress photos), which all read the full file into memory before writing.

## Baseline Behavior

`video_url` had no upload path anywhere — a nutritionist could only type/paste a URL. `save_upload` had no size limit and no video content-type mappings (video was never an upload type before this).

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro` spec `045-front-exercise-video-upload` (recording/picking UI). No `nutri_app` impact — playback stays external via `url_launcher`, identical whether `video_url` is a pasted link or this endpoint's own upload.

## Acceptance Criteria

1. Given a nutritionist uploads a video file, then `video_url` is returned and publicly fetchable (unauthenticated `/uploads/...` static mount) with the correct content-type.
2. Given a non-video file is uploaded, then the request is refused with `400`.
3. Given a file over 150 MB is uploaded, then the request is refused (mapped to `413`).
4. Given a patient token is used, then the request is refused (nutritionist-only, enforced at router level like the rest of `workout_plans`).

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 206/206 green (3 new `test_storage.py` cases covering the size guard).
- Live verification against the running backend: uploaded a real video file and confirmed the returned URL is fetchable with `video/mp4` content-type; confirmed a non-video file is rejected with `400`; confirmed a patient token is refused with `403`. Throwaway test accounts and the uploaded file cleaned up after.
