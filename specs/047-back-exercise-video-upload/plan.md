# Implementation Plan: Exercise Video Upload

**Branch**: `047-back-exercise-video-upload` | **Date**: 2026-08-25 | **Spec**: `specs/047-back-exercise-video-upload/spec.md`

## Summary

One new endpoint on the existing `workout_plans` router plus a small, backward-compatible extension to the shared `save_upload` helper.

## Steps

1. `app/core/storage.py`: `save_upload(file, *, subfolder, max_size_bytes=None)` — reads the file once, raises `ValueError` if `len(data) > max_size_bytes` before writing to disk. `_EXT_BY_CONTENT_TYPE` gains `video/mp4`→`.mp4`, `video/quicktime`→`.mov`, `video/webm`→`.webm`.
2. `app/modules/workout_plans/presentation/router.py`: `POST /exercise-videos` — already nutritionist-gated via the router's own `dependencies=[Depends(require_role("nutritionist"))]`. Validates `file.content_type.startswith("video/")` (400 otherwise), calls `save_upload(..., subfolder=f"workout_plans/{owner_id}/videos", max_size_bytes=150*1024*1024)`, catches `ValueError`→413, returns `{"video_url": ..., "content_type": ...}` (`response_model=dict`).
3. New `tests/test_storage.py`: unit tests for the new size guard, using a minimal in-memory `UploadFile` (`starlette.datastructures.Headers` for content-type) and a temp `UPLOADS_DIR`.

## Constraints

- `save_upload`'s new `max_size_bytes` param is optional and defaults to `None` (no limit) — every existing call site (logo, body-composition photos, progress photos) is unaffected.
- The endpoint is decoupled from any specific plan/exercise record — it returns a bare URL, embedded into an exercise sub-document only when the plan itself is later saved (a workout exercise has no id of its own to upload against).
