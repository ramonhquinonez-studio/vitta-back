# Feature Specification: Patient-Nutritionist Chat

**Feature Branch**: `042-back-patient-nutritionist-chat`
**Created**: 2026-08-25
**Status**: Draft
**Type**: Feature

## Objective

Phase 1 of the TrainerStudio gap analysis (following the completed Phase 0 multi-tenancy/billing foundation) — chat is TrainerStudio's headline "replace WhatsApp with an in-app conversation" feature, and Vitta had no messaging concept at all. This adds a minimal, polling-based (not WebSocket) message thread between a patient and their nutritionist, with push notification on new message reusing the existing (until now under-used) push pipeline.

## In Scope

- New `messaging` module: `Message` entity (`id, owner_id, patient_id, sender_role, text, created_at, read_at`), Mongo-backed repository scoped by the same `(owner_id, patient_id)` pair every other patient-scoped collection already uses.
- Nutritionist-side: `GET /patients/{patient_id}/messages?since=`, `POST /patients/{patient_id}/messages` (both nutritionist-role-gated, both verify the patient belongs to the caller before reading/writing — same defensive pattern as `appointments`' `patient_exists_for_owner`).
- Patient-side: `GET /me/messages?since=`, `POST /me/messages`, added to the existing `me` module (mirrors the established precedent — `me` queries shared collections directly with its own read/write logic rather than delegating to the sibling module's service, the same pattern already used for `appointments`/`measurements`/`hydration_logs`).
- Push notification on send, in both directions, reusing `send_push_to_tokens` directly (same call shape as `appointment_reminders.py`) — safe no-op today if the recipient has zero registered device tokens (true for every `nutri_pro` user until `040-front-push-foundation-and-chat` ships and a Firebase app is registered for it).

## Out of Scope

- No WebSocket/realtime transport — polling only (client polls `?since=<timestamp>` every ~15s while a thread is open, plus pull-to-refresh). No new backend dependency needed either way (uvicorn/FastAPI already carry WebSocket support if ever wanted, but nothing here uses it).
- No attachments, read receipts, or typing indicators in this pass — deliberately minimal v1.
- No `TestClient`/router-level integration tests — this repo's test suite is service-level-only by established convention (no `TestClient` infra exists anywhere), so live curl verification substitutes for that layer, as with every other feature this session.

## Baseline Behavior

No message/conversation data model existed anywhere in the stack. A patient and their nutritionist had no in-app way to communicate outside of consultation notes (nutritionist-authored, not a conversation) and appointment scheduling.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro` spec `040-front-push-foundation-and-chat` and `nutri_app` spec `048-front-nutritionist-chat`.

## Acceptance Criteria

1. Given a patient sends a message via `POST /me/messages`, when the nutritionist calls `GET /patients/{patient_id}/messages`, then it appears in the list.
2. Given a nutritionist sends a message via `POST /patients/{patient_id}/messages`, when the patient calls `GET /me/messages`, then it appears in the list.
3. Given a nutritionist who doesn't own a given patient, when calling `GET/POST /patients/{patient_id}/messages` for that patient, then it's refused with `404`.
4. Given a `since` timestamp is passed to either GET endpoint, then only messages created after it are returned.
5. Given either side sends a message, then a push is attempted to the recipient's registered device tokens — silently a no-op if they have none.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 160/160 green (5 new `test_messaging_service.py` cases, 4 new `me_service` message tests).
- Live verification against the running backend: registered a fresh patient via invite code, confirmed the full round trip both directions (patient→nutritionist, nutritionist→patient), confirmed a second, unrelated nutritionist gets `404` trying to read the thread, confirmed `since` filtering returns an empty list for a future timestamp. Test accounts cleaned up after.
