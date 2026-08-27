# Implementation Plan: Multi-Media Exercises (Backend)

**Branch**: `056-back-multi-media-exercises` | **Date**: 2026-08-26 | **Spec**: `specs/056-back-multi-media-exercises/spec.md`

## Summary

Pure schema-shape change plus a router endpoint widening — `mongo_workout_plans_repository.py`'s opaque `days` passthrough means zero repository code is touched (confirmed, same as `050-back-per-set-workout-authoring`).

## Steps

1. `app/schemas/workout_plan.py`: new `WorkoutMediaIn(BaseModel){url: str, media_type: str = Field(pattern="^(photo|video)$")}`; `WorkoutExerciseIn.video_url` removed, replaced with `media: List[WorkoutMediaIn] = Field(default_factory=list)`.
2. `app/modules/workout_plans/presentation/router.py`: `upload_exercise_video` → `upload_exercise_media` at `POST /workout-plans/exercise-media`; content-type check widened to accept `image/*` or `video/*` (error message updated: "El archivo debe ser una imagen o video."); `media_type = "photo" if content_type.startswith("image/") else "video"`; subfolder renamed `workout_plans/{owner_id}/media`; response body `{"url": ..., "media_type": ..., "content_type": ...}`.
3. No test file changes — confirmed no `video_url` references in `tests/test_workout_plans_service.py`.

## Constraints

- `exercise_library`'s own `video_url` field is untouched — separate module/collection.
