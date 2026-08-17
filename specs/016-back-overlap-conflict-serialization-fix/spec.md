# Bugfix Specification: Overlap-Conflict 409 Returns 500

**Feature Branch**: `016-back-overlap-conflict-serialization-fix`
**Created**: 2026-08-17
**Status**: Draft
**Type**: Bugfix

## Objective

`PATCH /appointments/{id}` (and `POST /appointments`) is supposed to return `409` with a structured `{code, message, conflict_id, conflict_start, conflict_end}` body when the new time overlaps an existing appointment. In practice it returned `500 Internal Server Error` with `"Object of type datetime is not JSON serializable"` — confirmed live while building `nutri_pro`'s appointment reschedule feature. This overlap path had apparently never been exercised successfully before (no test caught it — the existing `test_create_appointment_rejects_overlap` only asserts the exception is raised, never that the resulting HTTP response is well-formed).

## In Scope

- `AppointmentsService.conflict_detail()`: serialize `conflict_start`/`conflict_end` to ISO 8601 strings (`None`-safe for `conflict_end`) before returning, since `HTTPException`'s `detail` is rendered by Starlette's plain `json.dumps` — not FastAPI's Pydantic `response_model` machinery — and doesn't know how to encode `datetime`.
- Regression test asserting `json.dumps(conflict_detail(...))` succeeds and `conflict_start` is a `str`.

## Out of Scope

- Any other error-response shape in this codebase — this fix is scoped to the one dict that had raw `datetime` values passed straight into `HTTPException.detail`.

## Baseline Behavior

- `curl -X PATCH /appointments/{id} -d '{"start": ..., "end": ...}'` onto an occupied slot → `500`, `TypeError: Object of type datetime is not JSON serializable` in the server log.

## Target Design

- Same request → `409` with `{"detail": {"code": "OVERLAP", "message": "...", "conflict_id": "...", "conflict_start": "2026-08-16T17:53:18.214000", "conflict_end": "2026-08-16T18:38:18.214000"}}`.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given a reschedule/create request that overlaps an existing appointment, when submitted, then the response is `409` (not `500`) with a JSON-serializable `detail` object.
2. Given `conflict_end` is `None` (an appointment without an end time), when the conflict is serialized, then it doesn't raise.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 33/33 green (new: `test_conflict_detail_is_json_serializable`).
- Manual: reproduced the 500 live (`PATCH` onto Ramon's occupied slot), applied the fix, re-ran the identical request against the live dev server → clean `409` with the expected structured body.
