# Implementation Plan: Overlap-Conflict 409 Returns 500

**Branch**: `016-back-overlap-conflict-serialization-fix` | **Date**: 2026-08-17 | **Spec**: `specs/016-back-overlap-conflict-serialization-fix/spec.md`

## Summary

One-method fix: serialize datetimes before they reach `HTTPException.detail`.

## Steps

1. `app/modules/appointments/application/appointments_service.py#conflict_detail`: `.isoformat()` on `conflict_start`, `.isoformat() if ... else None` on `conflict_end`.
2. `tests/test_appointments_service.py`: `test_conflict_detail_is_json_serializable` — triggers a real `OverlapError`, calls `conflict_detail`, asserts `json.dumps(...)` doesn't raise and `conflict_start` is a `str`.

## Constraints

- No API contract change from the client's point of view — `conflict_start`/`conflict_end` were always documented/expected as datetime-shaped values; they just couldn't actually reach the client before this fix (the request 500'd first).
