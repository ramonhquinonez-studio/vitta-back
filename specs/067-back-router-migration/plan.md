# Implementation Plan: Migrate the 4 Remaining Fat Routers

**Feature Branch**: `067-back-router-migration`

## Summary

Four independent module migrations, each following the established target shape (mirroring `nutritionist_profile` for the simple ones, `billing` for `google_oauth`'s external-SDK isolation).

## Steps

1. **`app/modules/health/`**: `presentation/router.py` only (moved verbatim — two static-value endpoints, nothing to layer). `app/routers/health.py` → 1-line wrapper.
2. **`app/modules/users/`**: `domain/repositories.py` (`UsersRepository.get_user`), `application/users_service.py` (`UsersService.get_my_profile` — raises `LookupError` on not-found, defaults `role` to `"pro"` matching the original `_serialize_user`), `infrastructure/mongo_users_repository.py`, `presentation/router.py` (`GET /users/me`, `LookupError` → 404). `app/routers/users.py` → 1-line wrapper.
3. **`app/modules/devices/`**: `domain/repositories.py` (`DevicesRepository.register_device`/`.list_tokens_for_user`), `application/devices_service.py` (`DevicesService` — validates non-empty token, defaults platform to `"unknown"`), `infrastructure/mongo_devices_repository.py` (same upsert-by-`(user_id, token)` shape as the original), `presentation/router.py` (`POST /devices/register`, `POST /devices/test` — the latter still calls `app.core.notify.send_push_to_tokens` directly from the router, matching `me`/`messaging`'s existing convention rather than introducing a new abstraction for it). `app/routers/devices.py` → 1-line wrapper.
4. **`app/modules/google_oauth/`**: `domain/repositories.py` (`GoogleOAuthRepository.get_tokens`/`.save_tokens`/`.delete_tokens` — the last returns the deleted doc so the caller can revoke its token values with Google before they're gone locally), `infrastructure/mongo_google_oauth_repository.py`, `infrastructure/google_oauth_client.py` (wraps `Flow` construction/authorization-URL building/token exchange, and the revoke HTTP call — the only piece touching Google, mirroring `stripe_billing_provider.py`'s isolation of the Stripe SDK), `application/google_oauth_service.py` (`GoogleOAuthService` — owns the state-token JWT issue/decode logic and orchestrates connect/disconnect, calling the client + repository), `presentation/router.py` (`POST /oauth/start_url`, `GET /oauth/callback`, `GET /status`, `DELETE /disconnect`). `app/routers/google_oauth.py` → 1-line wrapper.
5. **`tests/test_router_wrapper_guardrails.py`**: `expected` dict gains all 4 new entries.
6. **`docs/modules/architecture.md`**: "Main Gaps"/"Applied Foundations"/"Pending Migration" (removed, nothing pending)/"Refactor Priority" updated to reflect 21/21.

## Constraints

- No `app/main.py` change needed — every router's `prefix`/route paths are unchanged; only their internal location moved, and `app/routers/<name>.py` still exports the same `router` object `main.py` already imports.
- No test fixture changes needed beyond the guardrail extension — this is a pure move with identical external behavior, verified live rather than via new unit tests (matching this codebase's established pattern for router-level behavior).
