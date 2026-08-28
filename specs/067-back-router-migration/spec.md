# Feature Specification: Migrate the 4 Remaining Fat Routers

**Feature Branch**: `067-back-router-migration`
**Created**: 2026-08-28
**Status**: Draft
**Type**: Refactor

## Objective

Closes the architecture-debt item flagged by `066-back-production-readiness-hardening`'s audit: 17 of 21 routers had already migrated to `app/modules/<feature>/{domain,application,infrastructure,presentation}/`, with `app/routers/<name>.py` reduced to a 1-line wrapper. `users`, `devices`, `google_oauth`, and `health` were the last four, confirmed by the audit to have no functional debt — purely structural inconsistency with the rest of the codebase. All four now migrated, closing the migration effort out completely (21/21).

## In Scope

- `app/modules/health/` — `presentation/router.py` only; no `domain`/`application`/`infrastructure` layers, since there's no business logic or persistence to separate (the two endpoints return static config values).
- `app/modules/users/` — full four-layer split. `UsersRepository` protocol, `UsersService.get_my_profile`, `MongoUsersRepository`, thin router.
- `app/modules/devices/` — full four-layer split. `DevicesRepository` protocol (register/list tokens), `DevicesService`, `MongoDevicesRepository`. The actual push-send call (`send_push_to_tokens`) stays in the presentation router, matching the existing convention already used by `me`/`messaging`'s routers rather than wrapping it in a new service method.
- `app/modules/google_oauth/` — full four-layer split, mirroring `billing`'s pattern of isolating an external SDK: `infrastructure/google_oauth_client.py` wraps the `Flow` object, token exchange, and Google's revoke endpoint (the only piece that talks to Google); `application/google_oauth_service.py` orchestrates the OAuth state-token JWT (issue/validate) and the connect/disconnect flow, calling the client and the `GoogleOAuthRepository` (Mongo-backed token storage).
- All four `app/routers/<name>.py` files reduced to the standard 1-line `from app.modules.<feature>.presentation.router import router` wrapper.
- `tests/test_router_wrapper_guardrails.py` extended with all four.
- `docs/modules/architecture.md` updated to reflect 21/21 migrated (was 17/21).

## Out of Scope

- Backfilling `test_router_wrapper_guardrails.py`'s list with the 6 already-migrated-but-never-added modules (`billing`, `checkin`, `messaging`, `workout_plans`, `exercise_library`, `nutrition_lookup`) — a separate, pre-existing documentation gap noted but not fixed here, to keep this slice scoped to the 4 routers actually being migrated.
- Fixing `app/core/notify.py`'s `send_push_to_tokens` — found while live-verifying `POST /devices/test` (`AttributeError: module 'firebase_admin.messaging' has no attribute 'send_multicast'`), but this is a pre-existing bug in code this migration didn't touch, unrelated to the router move. Flagged for a separate fix.

## Baseline Behavior

`users.py`, `devices.py`, `google_oauth.py`, `health.py` were standalone files directly under `app/routers/`, with no `app/modules/` package, HTTP handling and business logic mixed together in each.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`, `docs/modules/architecture.md` (already corrected as part of this spec).
- **Cross-repo impact**: none — internal backend refactor, no API contract change.

## Acceptance Criteria

1. Every endpoint previously served by the four old router files (`GET /users/me`, `POST /devices/register`, `POST /devices/test`, `POST /google/oauth/start_url`, `GET /google/oauth/callback`, `GET /google/status`, `DELETE /google/disconnect`, `GET /healthz`, `GET /version`) behaves identically — same paths, same request/response shapes.
2. `app/routers/users.py`, `devices.py`, `google_oauth.py`, `health.py` are each a single-line re-export wrapper.
3. `test_router_wrapper_guardrails.py`'s `test_legacy_routers_are_thin_wrappers` passes for all 21 entries, including the 4 new ones.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 227/227 green (no new tests needed beyond the guardrail extension — a pure refactor with identical external behavior, matching this codebase's established precedent that router-level upload/behavior smoke-checks happen via live verification, not new unit tests, for a pure move).
- Live verification against the running local server: `GET /healthz`, `GET /version`, `GET /users/me`, `POST /devices/register`, `GET /google/status`, `POST /google/oauth/start_url` (builds a real, correctly-signed Google authorization URL), `DELETE /google/disconnect` (correctly reports no tokens stored) — all confirmed working against the seeded demo account. `POST /devices/test` surfaced the pre-existing, unrelated `send_push_to_tokens` bug noted above (not introduced by this migration — confirmed by tracing the traceback into unchanged `app/core/notify.py`). QA device registration cleaned up after.
