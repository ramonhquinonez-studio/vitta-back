# Feature Specification: Session Photo on a Logged Workout Entry

**Feature Branch**: `062-back-workout-log-session-photo`
**Created**: 2026-08-27
**Status**: Draft
**Type**: Feature

## Objective

Deferred at `046-back-branding-and-session-logging` ("lower value-per-effort than the numeric/text fields"), before the per-set logging rewrite (`057-back-per-set-workout-logging`) replaced the flat/toggle `workout_logs` shape with a real per-exercise upsert. A photo field now persists correctly across edits under that shape (survives the coach's separate `coach_marked_done` toggle, since the two write paths stay isolated) in a way it structurally couldn't have before, so this closes the deferred item now.

## In Scope

- `photo_url`/`photo_content_type` on `WorkoutExerciseLogIn` and on the serialized `workout_logs` document (both the patient's own read via `GET /me/workout-logs` and the coach's read via `GET /patients/{id}/workout-logs`).
- New `POST /me/workout-logs/photo` — uploads an image via `save_upload`, returns `{"photo_url", "content_type"}`. A dedicated upload-then-reference endpoint (mirroring `POST /me/messages/attachment`'s shape), not inline multipart on `PUT /workout-logs/exercise`, since that endpoint is JSON-bodied and shared by every set-toggle/comment write.

## Out of Scope

- No content-type allow-list on the new upload endpoint — mirrors `POST /me/measurements`'s permissiveness (relies on `save_upload`'s own extension whitelist), not `POST /me/messages/attachment`'s explicit image/video/PDF gate, since a session photo is image-only by convention (like every other "photo" field in this codebase).
- No migration of existing `workout_logs` documents — same precedent as `057`: dev DB has no real log data needing backfill; missing fields simply read as `null`.
- Per-set photos — one photo per exercise entry (the same doc `comment` already lives on), not per individual set.

## Baseline Behavior

Post-`057`, `workout_logs` documents hold `sets`, `comment`, `coach_marked_done`, `updated_at` — no photo field anywhere in the schema, repository, or serializer.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_app`'s `061-front-workout-log-session-photo` consumes this contract (upload + view); `nutri_pro`'s `068-front-workout-log-session-photo-display` consumes the read side only.

## Acceptance Criteria

1. Given a patient uploads a photo via `POST /me/workout-logs/photo`, then the response contains a `photo_url` under `/uploads/workout_logs/{patient_user_id}/...`.
2. Given that `photo_url` is included in a subsequent `PUT /me/workout-logs/exercise` call, then `GET /me/workout-logs` returns it on the matching entry.
3. Given the owning nutritionist calls `GET /patients/{patient_id}/workout-logs`, then the same `photo_url`/`photo_content_type` appear on the read-only coach side.
4. Given no photo was ever attached, then both fields serialize as `null`, not absent keys.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 225/225 green (one new pass-through assertion in `test_me_service.py`'s fake repo/tests; `test_patients_service.py` unaffected — its fake operates above the real serializer).
- Live verification against the running local server: logged in as the seeded demo nutritionist/patient (`pro_demo@nutri.app`/`patient_demo@nutri.app`, `app/scripts/seed_dev.py`), created and assigned a throwaway workout plan, exercised the full round trip — upload → `PUT` with the returned URL → `GET /me/workout-logs` → `GET /patients/{id}/workout-logs` → direct fetch of the served file (`200 image/jpeg`) — then deleted the throwaway plan, its `workout_logs` document, and the uploaded file.
- **Aside found during verification, fixed as a follow-up (not part of this slice's own scope, done separately at the user's request)**: the seeded demo nutritionist account (`seed_dev.py`) was created with `role: "pro"`, but `require_role("nutritionist")` (added after that seed script was written) gates every nutritionist-only route including `/patients` and `/workout-plans` on the literal string `"nutritionist"`. Fixed: `seed_dev.py` now passes `role="nutritionist"`; since `upsert_user` only inserts on first creation and never updates an existing record, the already-seeded dev DB account also needed a one-time direct correction, applied and verified live (`pro_demo@nutri.app` logs in with `role: "nutritionist"`, `GET /patients` → `200`).

## Documentation

- New `nutri_back/specs/062-back-workout-log-session-photo/{spec.md,plan.md,tasks.md}`, `SPEC_ROADMAP.md` append.
