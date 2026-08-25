# Feature Specification: Tenant Isolation & Authorization Hardening

**Feature Branch**: `040-back-tenant-isolation-hardening`
**Created**: 2026-08-24
**Status**: Draft
**Type**: Hardening

## Objective

Vitta is moving toward a multi-tenant SaaS model (many independent nutritionists, each an isolated tenant identified by their own `owner_id`). A codebase audit (3 parallel research passes) found the existing `owner_id` scoping pattern already does most of the isolation work correctly, but surfaced concrete gaps worth closing before more tenants — and real billing — depend on it: two Mongo calls in `appointments` that relied on a prior ownership check rather than filtering by `owner_id` themselves; several patient-scoped collections with no explicit tenant field; and a `role` field decoded from every JWT but never actually checked by any route.

## In Scope

- `appointments/infrastructure/mongo_appointments_repository.py`: `delete_for_owner`'s final `delete_one` and `set_google_event_id` both gain `owner_id` in their Mongo filter (previously `_id`-only).
- `app/core/deps.py`: new `require_role(*roles)` dependency factory, applied to every nutritionist-only router (`patients`, `plans`, `recipes`, `appointments`, `recommendations`, `consultations`, `nutritionist_profile`, `nutrition_lookup`, `billing`) and to the write endpoints of the two mixed-access routers (`equivalencies`' `create_food`/`delete_food`, `content_library`'s `articles/mine`/`create`/`update`/`delete`). Platform-shared reads (`/equivalencies/groups`, `/equivalencies/foods` GET, `/content/articles` GET) and every `/me/*` route (patient-facing, resolves identity server-side) are untouched.
- `hydration_logs`: gains explicit `owner_id` stamping at write time (`add_hydration`) — `measurements`, `body_compositions`, and `food_diary_entries` were confirmed to already stamp it.
- Lightweight Mongo-backed rate limiting (`app/core/rate_limit.py`) on `POST /auth/register` and `POST /auth/register-nutritionist` — 10 attempts/hour/IP, TTL-indexed so no cleanup job is needed.

## Out of Scope

- No new `owner_id` **read-side** filters added to `measurements`/`body_compositions`/`food_diary_entries`/`hydration_logs` beyond what already exists — every read in the `me` module resolves `patient_id` server-side from the authenticated user's own record (verified: no endpoint anywhere in `me/presentation/router.py` accepts a client-supplied `patient_id` or `owner_id`), so `patient_id`-only reads are already tenant-safe. Adding a strict `owner_id` filter on top would risk silently hiding any pre-existing document from before this stamping was consistent, for a scenario (a bug bypassing that resolution) the resolution itself already prevents.
- No Tenant/Organization entity — the nutritionist's own `user_id` continues to be the tenant boundary (see `041-back-billing-foundation`'s design decision).
- `prescriptions`/`clinical_notes`: confirmed read-only today (no write path exists anywhere), so there's nothing to stamp yet.

## Baseline Behavior

`role` was decoded from every JWT but never checked — a patient-role account could call any nutritionist-only endpoint (scoped to their own id as if it were an `owner_id`, which is nonsensical but not a cross-tenant leak, since the isolation is by id not by role). `appointments`' delete and Google-sync-id paths had no defense-in-depth against a caller reaching them without the preceding ownership check. `hydration_logs` had no tenant field at all. Public registration endpoints had no rate limiting.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: none — backend-only hardening, no contract change for either Flutter app.

## Acceptance Criteria

1. Given a valid nutritionist JWT, when calling any route under `/patients`, `/plans`, `/recipes`, `/appointments`, `/recommendations`, `/consultations`, `/nutritionist_profile`, `/nutrition`, `/billing`, then it succeeds as before.
2. Given a valid patient JWT, when calling any of those same routes directly, then it's rejected with `403`.
3. Given a valid patient JWT, when calling `/me/*` or `/equivalencies/groups`/`/equivalencies/foods` (GET), then it's unaffected.
4. Given 11 registration attempts from the same IP within an hour, then the 11th is rejected with `429`.
5. Given a patient logs hydration, then the created/updated `hydration_logs` document carries the correct `owner_id`.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 132/132 green at the end of this slice (2 new appointments tests, 3 new require_role tests; full backend suite grows further with `041`).
- Live verification against the running backend: nutritionist token succeeds on `/patients`, patient token gets `403`; `/me/appointments` and `/equivalencies/groups` unaffected for the patient token; `/equivalencies/foods` POST correctly `403`s for a patient; 11 rapid `POST /auth/register-nutritionist` calls from the same IP — 10 succeed, 11th returns `429`.
