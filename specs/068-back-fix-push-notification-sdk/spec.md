# Feature Specification: Fix Push Notification SDK Call

**Feature Branch**: `068-back-fix-push-notification-sdk`
**Created**: 2026-08-28
**Status**: Draft
**Type**: Bug Fix

## Objective

Found live while verifying `067-back-router-migration`'s migrated `POST /devices/test` endpoint: `app/core/notify.py`'s `send_push_to_tokens` called `messaging.send_multicast`, which was removed in `firebase-admin` 7.x (Google deprecated the underlying FCM batch API) — every call raised `AttributeError: module 'firebase_admin.messaging' has no attribute 'send_multicast'`. Confirmed pre-existing and unrelated to the router migration (unchanged code, same bug present before and after that move). This means **no push notification has ever actually sent** since whatever point the installed SDK version passed 7.0 — every call site (`me`/`messaging`/`devices` routers) silently 500'd or, worse, was wrapped in a broad except and swallowed.

## In Scope

- `send_push_to_tokens` now calls `messaging.send_each_for_multicast` instead — the direct replacement (same `MulticastMessage` input, same `BatchResponse` output, confirmed present on the installed `firebase-admin==7.1.0`).
- New `tests/test_notify.py` — locks in the correct method name via a mock, plus the two existing early-return paths (no app initialized, no tokens).

## Out of Scope

- No change to any call site (`me`, `messaging`, `devices` routers) — they already handle the return value correctly (or ignore it, which remains fine since `send_each_for_multicast`'s `BatchResponse` shape matches what `send_multicast` returned).

## Baseline Behavior

Every push-send attempt raised an unhandled `AttributeError`, surfacing as a 500 to whichever endpoint triggered it.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: none — internal backend fix, no API contract change (the endpoint's request/response shape is unchanged, it just now actually works).

## Acceptance Criteria

1. `send_push_to_tokens` calls `messaging.send_each_for_multicast`, not the removed `send_multicast`.
2. `POST /devices/test` returns `200 {"ok": true, "sent_to": N}` instead of `500`, given at least one registered device token.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 230/230 green (227 previous + 3 new `test_notify.py` tests).
- Live verification against the running local server (which has a real `firebase-service-account.json` configured): registered a throwaway device token, called `POST /devices/test`, confirmed `200 {"ok":true,"sent_to":1}` (previously `500`). Throwaway device registration cleaned up after.
