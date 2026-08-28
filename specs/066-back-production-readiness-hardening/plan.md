# Implementation Plan: Production-Readiness Hardening

**Feature Branch**: `066-back-production-readiness-hardening`

## Summary

Six independent fixes surfaced by a dedicated audit fork, applied directly (each small and self-contained).

## Steps

1. **`app/core/storage.py`**: `save_upload` derives `ext` only from `_EXT_BY_CONTENT_TYPE.get(content_type, ".bin")`, removing the `Path(file.filename or "").suffix` fallback entirely.
2. **Five router files** (`me/presentation/router.py` ×2, `plans/presentation/router.py`, `patients/presentation/router.py`, `nutritionist_profile/presentation/router.py`): each `save_upload` call site wrapped in `try/except ValueError` → `HTTPException(413, ...)`, with a `max_size_bytes` added (15MB photos, 25MB PDF/report, 5MB logo).
3. **`app/modules/auth/presentation/router.py`**: `dependencies=[Depends(rate_limit("login", limit=20, window_seconds=3600))]` on `/login`; `dependencies=[Depends(rate_limit("forgot-password", limit=5, window_seconds=3600))]` on `/forgot-password`.
4. **`app/core/config.py`** `validate_security_baseline`: new check — `if not self.CORS_ORIGINS: raise ValueError(...)` inside the existing `app_env in ("prod", "production", "staging")` branch.
5. **`app/modules/messaging/application/messaging_service.py`**: new `ensure_patient_belongs_to_owner(owner_id, patient_id)` wrapping the existing `repository.patient_exists_for_owner` check. **`app/modules/messaging/presentation/router.py`** `upload_message_attachment`: calls it before `save_upload`, `LookupError` → `404`.
6. **`docs/modules/architecture.md`**: rewritten "Main Gaps"/"Applied Foundations"/"Pending Migration"/"Refactor Priority" sections to reflect the real 17/21-migrated state (verified via `ls app/modules/` cross-referenced against `wc -l app/routers/*.py`).
7. **`tests/test_storage.py`**: two new regression tests locking in the content-type-spoofing fix (spoofed filename → content-type-derived extension; unrecognized content-type → `.bin` fallback).

## Constraints

- No test changes needed for items 2-5 beyond the storage tests — existing service-level tests fake the whole repository/service layer and don't exercise the router's multipart/size-limit wiring directly (matches this codebase's established precedent of live-verifying router-level upload behavior instead).
