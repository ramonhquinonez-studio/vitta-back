# Implementation Plan: Public (Licensed) Exercise Library (Backend)

**Branch**: `059-back-public-exercise-library` | **Date**: 2026-08-26 | **Spec**: `specs/059-back-public-exercise-library/spec.md`

## Summary

Additive schema-and-endpoint change on `exercise_library`, a WorkoutX client, a quota-aware sync script, and a fetch-once-cache-forever video resolution endpoint.

## Steps

1. `app/modules/exercise_library/infrastructure/mongo_exercise_library_repository.py`: `list_platform_items()` (`find({"owner_id": None})`), `get_platform_item(item_id)` (looks up by string `_id`, not `_as_oid` — platform items keep WorkoutX's own id as a stable string like `"workoutx-0001"`), `update_platform_item_video_url(item_id, video_url)`.
2. `app/modules/exercise_library/domain/repositories.py`: all three added to the `Protocol`.
3. `app/modules/exercise_library/infrastructure/workoutx_client.py`: `WorkoutXClient` — `list_exercises(limit, offset)` (full data per item, confirmed live), `fetch_gif_bytes(gif_url)` (needs `X-WorkoutX-Key`, confirmed 401 without it / 200 with it).
4. `app/core/storage.py`: `save_bytes(data, subfolder, filename)` — persists arbitrary fetched bytes (as opposed to `save_upload`'s client-`UploadFile` path).
5. `app/modules/exercise_library/application/exercise_library_service.py`: `list_platform_items()`; `get_platform_video_url(item_id)` — returns the cached relative `/uploads/...` URL immediately if already cached (`video_url.startswith("/uploads/")`), otherwise fetches via `WorkoutXClient`, caches via `save_bytes`, persists the rewrite, and returns the new relative URL.
6. `app/modules/exercise_library/presentation/router.py`: `GET /exercise-library/platform`; `GET /exercise-library/platform/{item_id}/video-url` (takes `Request` to prefix the relative cached URL with `request.base_url` before returning — GIFs need an absolute URL to load via `Image.network`, unlike this codebase's existing convention of returning bare relative `/uploads/...` paths elsewhere).
7. `app/core/config.py`: `WORKOUTX_API_KEY: str = ""`.
8. New `app/scripts/sync_workoutx_exercise_library.py`: paginated `list_exercises` loop (100/page), `--limit` flag, stores `gifUrl` as-is (uncached) plus a `notes` string assembled from `bodyPart`/`target`/`equipment`/`instructions`.
9. `tests/test_exercise_library_service.py`: platform-items tests plus `get_platform_video_url` tests (mocking `WorkoutXClient`/`save_bytes` — cache-on-first-call and reuse-if-already-cached cases).

## Constraints

- `WorkoutXClient`/the sync script/the video-url endpoint are all WorkoutX-specific today — an earlier iteration built the equivalent against MuscleWiki (mint-a-short-lived-token model) before the user redirected to the free-tier vendor; that code was fully removed, not left dead, once the pivot was confirmed.
- Free-tier-only commitment — WorkoutX's terms restrict free-tier use to evaluation; flag this again before any real production rollout.
