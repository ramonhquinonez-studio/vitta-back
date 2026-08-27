# Implementation Plan: Chat Photo Attachments + Per-Patient Nutrition Goals

**Branch**: `049-back-chat-attachments-and-patient-goals` | **Date**: 2026-08-25 | **Spec**: `specs/049-back-chat-attachments-and-patient-goals/spec.md`

## Summary

Two independent, small extensions bundled into one slice: optional attachment fields threaded through both message-send paths plus a new upload endpoint on each, and four optional goal fields added to `Patient`'s existing update flow.

## Steps

### Chat attachments
1. `app/schemas/messaging.py`: `MessageIn.text` becomes optional (default `""`); both schemas gain `attachment_url`/`attachment_type`.
2. `messaging/domain/entities.py` + `domain/repositories.py` + `infrastructure/mongo_messaging_repository.py`: `Message`/`create()` gain the two fields end-to-end.
3. `messaging/application/messaging_service.py::send_from_nutritionist`: accepts the two fields, validation becomes "text or attachment_url required".
4. `messaging/presentation/router.py`: `send_message` passes the fields through; new `POST /{patient_id}/messages/attachment` (image-only, 25 MB cap, mirrors `workout_plans`' video-upload endpoint shape).
5. Mirror steps 2–4 on the `me` side: `me/domain/repositories.py` + `infrastructure/mongo_me_repository.py::create_message` + `application/me_service.py::send_message` + `presentation/router.py` (`POST /me/messages/attachment`).
6. Tests: `test_messaging_service.py` and `test_me_service.py` fakes updated; one new attachment-only-send case each.

### Patient nutrition goals
1. `patients/domain/entities.py`: `Patient` gains the four optional goal fields.
2. `patients/infrastructure/mongo_patients_repository.py::_to_entity`: maps them.
3. `app/schemas/patients.py`: `PatientUpdate`/`PatientOut` gain the four fields (bounded `Field(..., ge=0, le=...)` ranges, matching the existing validation style on `age`/`height_cm`).
4. `patients/presentation/router.py::_serialize`: includes them in `PatientOut`. No router/service change needed beyond that — `update_patient`'s existing `{k: v for k, v in payload.model_dump().items() if v is not None}` filter already handles partial goal updates the same way it handles every other optional field.
5. `me/infrastructure/mongo_me_repository.py::get_patient_for_user`: also gains the four fields — this is a separate, hand-built serialization dict (not shared with `patients`' `_to_entity`), and it's the one `GET /me/profile` (the patient's own read of themselves) actually uses. Missed on the first pass since it lives in a different module; caught via live verification, not a unit test (this dict has no dedicated test coverage — `MeService.get_profile` is a pure passthrough to the repository).
6. Tests: `test_patients_service.py`'s fake `update_for_owner` carries the fields through; one new round-trip test.

## Constraints

- A message needs *either* text or an attachment — never neither. Both send paths enforce this identically.
- No goal-value validation beyond simple bounds (`Field(ge=..., le=...)`) — no cross-field consistency check (e.g., protein+carbs+fat kcal roughly matching `daily_kcal_goal`), matching how this codebase doesn't cross-validate macros elsewhere either.
