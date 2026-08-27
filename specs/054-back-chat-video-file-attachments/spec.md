# Feature Specification: Video/File Chat Attachments (Backend)

**Feature Branch**: `054-back-chat-video-file-attachments`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

Chat attachments were images-only, explicitly flagged: "Video/file chat attachments — `047-front-quick-wins` is photos only, by design." `app/core/storage.py`'s `save_upload` already had an extension map covering video (`mp4`/`mov`/`webm`) and `application/pdf` alongside images — it was already prepared for this, just never unlocked at the router level.

## In Scope

- Both message-attachment upload endpoints (`POST /patients/{patient_id}/messages/attachment` nutritionist-side, `POST /me/messages/attachment` patient-side) now accept images, videos, and PDFs instead of images only.

## Out of Scope

- No broader file-type support than what `storage.py` can already extension-map (images, `video/mp4`/`video/quicktime`/`video/webm`, `application/pdf`) — not opening this up to arbitrary file types.
- No `max_size_bytes` change (stays 25MB) — not explicitly asked to raise, and generous enough for short clips/documents.
- No schema change — `attachment_url`/`attachment_type` were already unconstrained strings.

## Baseline Behavior

Both endpoints rejected any non-image upload with `400 "El archivo debe ser una imagen."`, even though the storage layer already knew how to handle video/PDF extensions.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` and `nutri_app` spec `057-front-chat-video-file-attachments` (both) consume this.

## Acceptance Criteria

1. Given a nutritionist or patient uploads a `.mp4`/`.mov`/`.webm` file to their respective attachment endpoint, then it's accepted and stored, same as an image.
2. Given a `.pdf` upload, then it's accepted and stored.
3. Given any other file type (e.g. plain text), then the endpoint still rejects it with `400` and an updated message: "El archivo debe ser una imagen, video o PDF."

## Validation

- Full backend unittest suite green (no test file changes — this validation lives in the router, not the service layer, matching this codebase's convention of service-level unit tests only).
- Live-curl verification against the running local server: uploaded a fake `.mp4` and `.pdf` through both endpoints (accepted, correct `content_type` echoed back), confirmed a `.txt` upload still rejected with 400 on both. Test data cleaned up afterward.
