# Implementation Plan: Video/File Chat Attachments (Backend)

**Branch**: `054-back-chat-video-file-attachments` | **Date**: 2026-08-26 | **Spec**: `specs/054-back-chat-video-file-attachments/spec.md`

## Summary

A one-line widening of the content-type gate in both attachment-upload router handlers, matching exactly what `app/core/storage.py`'s `_EXT_BY_CONTENT_TYPE` map already supports.

## Steps

1. `app/modules/messaging/presentation/router.py` (`upload_message_attachment`): `content_type.startswith("image/")` → `content_type.startswith("image/") or content_type.startswith("video/") or content_type == "application/pdf"`; error message updated to "El archivo debe ser una imagen, video o PDF."
2. `app/modules/me/presentation/router.py` (`upload_my_message_attachment`): identical change.

## Constraints

- No changes to `save_upload`/`_EXT_BY_CONTENT_TYPE` (`app/core/storage.py`) — already correctly configured for this.
- No changes to `MessageIn`/`MessageOut`/domain `Message` — `attachment_url`/`attachment_type` were already unconstrained strings.
