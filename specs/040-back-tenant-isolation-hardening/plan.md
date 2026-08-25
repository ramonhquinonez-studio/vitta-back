# Implementation Plan: Tenant Isolation & Authorization Hardening

**Branch**: `040-back-tenant-isolation-hardening` | **Date**: 2026-08-24 | **Spec**: `specs/040-back-tenant-isolation-hardening/spec.md`

## Summary

Close the specific gaps a 3-agent codebase audit found, without inventing new abstractions — every fix reuses the existing `owner_id`/`_as_oid` pattern already used consistently across the codebase.

## Steps

1. `appointments/domain/repositories.py` + `infrastructure/mongo_appointments_repository.py`: `set_google_event_id` gains an `owner_id` parameter, used in both its Mongo filter and its confirming read; `delete_for_owner`'s `delete_one` filter gains `owner_id`. Both call sites in `appointments_service.py` updated to pass `owner_id` through.
2. `app/core/deps.py`: `require_role(*roles)` — a dependency factory returning an async check that raises `403` when `current["role"]` isn't in `roles`.
3. Apply `dependencies=[Depends(require_role("nutritionist"))]` at the `APIRouter(...)` level for `patients`, `plans`, `recipes`, `appointments`, `recommendations`, `consultations`, `nutritionist_profile`, `nutrition_lookup`; apply it per-route for `equivalencies`' two write endpoints and `content_library`'s four owner-scoped endpoints (its public `GET /content/articles` stays as-is).
4. `me/domain/repositories.py` + `infrastructure/mongo_me_repository.py` + `application/me_service.py`: `add_hydration` gains an `owner_id` parameter, stamped via `$set` on the hydration-log upsert (not `$setOnInsert`, so it backfills existing documents too).
5. `app/core/rate_limit.py`: `rate_limit(bucket, *, limit, window_seconds)` dependency factory — counts recent `rate_limit_events` docs for `(bucket, ip)`, inserts one per call, raises `429` at the limit. `app/db/init_indexes.py` gets a TTL index on `rate_limit_events.at` (3600s) plus a plain index on `key`.
6. Applied to `/auth/register` and `/auth/register-nutritionist` via `dependencies=[Depends(rate_limit(...))]`.

## Constraints

- No behavior change for any route already correctly scoped — this is defense-in-depth and closing a real (if not yet exploited) gap, not a redesign.
- `require_role` composes with `get_current_user` (FastAPI caches the JWT decode within one request, so no double-decode cost).
