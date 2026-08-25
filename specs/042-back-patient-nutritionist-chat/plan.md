# Implementation Plan: Patient-Nutritionist Chat

**Branch**: `042-back-patient-nutritionist-chat` | **Date**: 2026-08-25 | **Spec**: `specs/042-back-patient-nutritionist-chat/spec.md`

## Summary

A new `messaging` module for the nutritionist-side endpoints, plus additions to the existing `me` module for the patient-side ones — following the two established composition patterns in this codebase exactly (dedicated module for a bounded context; `me` duplicating read/write logic against a shared collection rather than delegating to a sibling module's service).

## Steps

1. `messaging/domain/entities.py`: `Message` dataclass.
2. `messaging/domain/repositories.py`: `MessagingRepository` Protocol (`list_for_thread`, `create`, `patient_exists_for_owner`).
3. `messaging/infrastructure/mongo_messaging_repository.py`: standard `_as_oid`-scoped CRUD against `messages`.
4. `messaging/application/messaging_service.py`: `list_for_thread`/`send_from_nutritionist`, both verify `patient_exists_for_owner` first (404 otherwise).
5. `app/schemas/messaging.py`: `MessageOut`/`MessageIn`.
6. `messaging/presentation/router.py`: own `APIRouter(prefix="/patients", ..., dependencies=[Depends(require_role("nutritionist"))])` — a second router instance sharing the `/patients` prefix with the existing `patients` router (no path collision, since it only adds `/{patient_id}/messages`), pushing the patient's tokens on send.
7. `app/routers/messaging.py` wrapper + `main.py` wiring.
8. `app/db/init_indexes.py`: compound `(owner_id, patient_id, created_at)` index on `messages`.
9. `me/domain/repositories.py` + `infrastructure/mongo_me_repository.py`: `list_messages`/`create_message`, reading/writing the same `messages` collection directly (same document shape as the `messaging` module's repository, so both sides interoperate).
10. `me/application/me_service.py`: `list_messages`/`send_message` (`send_message` requires a linked nutritionist — raises `LookupError` otherwise) + a small public `get_my_patient_record` so the router can resolve the owner id for pushing without reaching into the service's private repository.
11. `me/presentation/router.py`: `GET/POST /me/messages`, pushing the nutritionist's tokens on send.
12. Tests: `tests/test_messaging_service.py` (fake repository), extensions to `tests/test_me_service.py`.

## Constraints

- Both sides' write paths independently stamp the exact same document shape (`owner_id, patient_id, sender_role, text, created_at, read_at`) into the same `messages` collection — this duplication is deliberate, matching the established `me`-module precedent, not an oversight.
- Push failures never surface as an error to the sender — `send_push_to_tokens` already no-ops safely on an empty token list or missing Firebase config.
