# Feature Specification: Public (Licensed) Exercise Library (Backend)

**Feature Branch**: `059-back-public-exercise-library`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

`exercise_library` was 100% nutritionist-authored, by explicit prior design (`044-front-branding-and-exercise-library`: "not a licensed database"). The user wants a TrainerStudio-style two-section exercise picker — "Mi biblioteca" (unchanged) plus a "Biblioteca pública" backed by a licensed exercise database, mirroring the one existing precedent for this split in the app: `content_library`'s `Article.owner_id: Optional[str]` (`null` = platform, set = nutritionist-authored), merged via `MongoMeRepository.list_articles()`.

**Vendor note**: MuscleWiki was evaluated first but requires a paid TESTING tier ($10/mo) for direct API access (confirmed live — the free BASIC tier returns `403 "BASIC tier is restricted to playground access only"`). Landed on **WorkoutX** instead (free tier: 500 calls/month, no credit card) after also ruling out ExerciseDB/AscendAPI (requires RapidAPI signup for production access, and the data itself is AGPL-3.0 licensed — a copyleft license that can force open-sourcing a network service that uses it). WorkoutX's own FAQ states the free tier is for "evaluation and small projects" — commercial production use needs a paid plan; revisit before relying on this at real scale.

## In Scope

- `exercise_library` documents with `owner_id: None` are now a recognized "platform" tier, additive to the existing owner-scoped documents.
- `GET /exercise-library/platform` — any authenticated nutritionist, returns platform items only, same `ExerciseLibraryItemOut` shape as the existing owner-scoped endpoint.
- `app/scripts/sync_workoutx_exercise_library.py` — idempotent upsert-by-stable-id sync script (not a public endpoint, run manually), mirrors `seed_content_library.py`'s pattern. Confirmed live: WorkoutX's `GET /v1/exercises` returns full exercise data (name, gifUrl, bodyPart, equipment, instructions) in one call — no per-exercise detail call needed, so a full ~1,327-exercise sync costs only ~14 calls (well inside the free quota).
- `GET /exercise-library/platform/{item_id}/video-url` — resolves a directly-playable URL for a platform item's GIF. WorkoutX's `gifUrl` values 401 without our permanent API key on every fetch (confirmed live), and they offer no lower-privilege short-lived-token option (unlike MuscleWiki's `/media/token`), so this endpoint **caches the GIF into our own `/uploads` storage on first request** and rewrites the item's stored `video_url` to the cached path — every call after the first is a plain DB lookup, at most one WorkoutX call ever per exercise, not per view. Confirmed live end-to-end: first call fetches+caches, the cached URL then loads with zero auth.
- `app/core/storage.py`: new `save_bytes()` helper (sibling to `save_upload`, for persisting fetched-not-uploaded bytes).
- `WorkoutXClient` (`app/modules/exercise_library/infrastructure/workoutx_client.py`): thin client wrapping `list_exercises`/`fetch_gif_bytes`.

## Out of Scope

- No patient-facing exposure — `nutri_app` is untouched; patients still only see exercises via an assigned workout plan. (Once a coach adds a public exercise to an assigned plan, a patient would need the same URL-resolution step — deferred to a future slice.)
- No commitment to WorkoutX beyond their free tier — their own terms restrict the free tier to evaluation; a real production rollout needs the user to review and likely upgrade to a paid plan first.

## Baseline Behavior

`exercise_library` had no `owner_id: None`/platform concept; `GET /exercise-library` was always owner-scoped, and there was no way to browse externally-sourced content.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` spec `064-front-public-exercise-library` consumes both endpoints.

## Acceptance Criteria

1. Given no platform items exist, when a nutritionist calls `GET /exercise-library/platform`, then it returns `[]`.
2. Given platform items exist (`owner_id: None`), then `GET /exercise-library/platform` returns them, sorted by name, and `GET /exercise-library` (owner-scoped) does not include them.
3. Given a platform item's video is requested for the first time, then it's fetched from WorkoutX, cached locally, and the returned URL loads with no auth. Given it's requested again, then no further WorkoutX call is made.
4. Given the sync script runs without `WORKOUTX_API_KEY` set, then it raises a clear error rather than silently no-op'ing.

## Validation

- Full backend unittest suite green (224/224).
- Live-curl verification against the running local server: confirmed `GET /exercise-library/platform` empty on a clean collection; ran `sync_workoutx_exercise_library.py --limit 5` against the real WorkoutX API (5 real exercises synced, real data confirmed via `GET /exercise-library/platform`); confirmed `GET /exercise-library/platform/{id}/video-url` fetches+caches on first call and the returned cached URL loads with zero auth headers. Real synced data was kept (useful seed content, not throwaway); only the QA nutritionist test account was cleaned up afterward.
