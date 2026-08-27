# Feature Specification: Chat Photo Attachments + Per-Patient Nutrition Goals

**Feature Branch**: `049-back-chat-attachments-and-patient-goals`
**Created**: 2026-08-25
**Status**: Draft
**Type**: Feature

## Objective

Two of the "quick wins" from the "Vitta vs. TrainerStudio" parity report: chat could only carry text (TrainerStudio advertises file/photo sharing in-thread), and there was no way to set a patient's daily calorie/macro targets (only per-food-item macros existed, never a per-client goal).

## In Scope

- `messages` documents (both `me`'s patient-side thread and `messaging`'s nutritionist-side thread — the same collection, two write paths) gain optional `attachment_url`/`attachment_type`. A message needs *either* non-blank text *or* an attachment — not both required.
- New upload endpoints mirroring the exercise-video pattern exactly, image-only, 25 MB cap: `POST /me/messages/attachment` (patient) and `POST /patients/{patient_id}/messages/attachment` (nutritionist), both returning `{attachment_url, content_type}`.
- `Patient` gains `daily_kcal_goal`, `daily_protein_g_goal`, `daily_carbs_g_goal`, `daily_fat_g_goal` (all optional floats), wired through the **existing** `PATCH /patients/{id}` — no new endpoint, same pattern as updating `notes`/`allergies`.
- The goal fields also flow through to the patient's own read of themselves: `GET /me/profile`'s `patient` sub-object (`MongoMeRepository.get_patient_for_user`, a separately hand-built serialization dict from the one `patients` module uses) gained the same four fields — needed so `nutri_app` can display "consumed vs. goal" without a new endpoint.

## Out of Scope

- No video/file attachments in chat — images only (`content_type` must start with `image/`), matching the "photo attachment" framing of the original ask.
- No automatic goal computation (e.g., from age/weight/activity level via a formula) — the nutritionist sets the numbers directly, same as every other manually-entered field on `Patient`.
- No `nutri_app`-side "actual vs. goal" computation on the backend — that's done client-side from data the app already fetches (see `053-front-chat-attachments-and-goals`).

## Baseline Behavior

`MessageIn`/`MessageOut` only ever carried `text`. `Patient` had no nutrition-goal concept at all — food-diary entries and plan items had per-entry/per-item `kcal`/macros, never an aggregate daily target.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro` spec `047-front-quick-wins` and `nutri_app` spec `053-front-chat-attachments-and-goals`.

## Acceptance Criteria

1. Given either side uploads a photo and sends it with no text, then the message is accepted and both `GET .../messages` reads show the attachment fields.
2. Given a non-image file is uploaded to either attachment endpoint, then it's rejected with `400`.
3. Given a nutritionist sets a patient's `daily_kcal_goal`, then it round-trips through `GET`/`PATCH` unchanged, and other goal fields stay `null` until explicitly set.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 210/210 green (3 new cases: patient goal round-trip, nutritionist-side attachment-only send, patient-side attachment-only send).
- Live verification against the running backend: set all four goal fields and confirmed the exact values round-tripped; uploaded a real image, sent it as a message with no text, confirmed both message-list reads show the attachment fields and the URL is fetchable (`200 image/jpeg`); confirmed a non-image upload is rejected with `400`. Test account/data cleaned up after.
