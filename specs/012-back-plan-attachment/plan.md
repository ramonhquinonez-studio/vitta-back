# Implementation Plan: Plan Attachment

**Branch**: `012-back-plan-attachment` | **Date**: 2026-08-15 | **Spec**: `specs/012-back-plan-attachment/spec.md`

## Summary

Add attachment fields to `plans` and a multipart upload endpoint, reusing the InBody attachment pattern verbatim.

## Steps

1. `app/schemas/plan.py`: `PlanOut.attachment_url`/`attachment_type` (optional).
2. `app/modules/plans/domain/repositories.py`: add `set_attachment_for_owner` to the `PlansRepository` protocol.
3. `app/modules/plans/infrastructure/mongo_plans_repository.py`: `_serialize` includes both fields; `set_attachment_for_owner` delegates to existing `update_for_owner`.
4. `app/modules/plans/application/plans_service.py`: `set_attachment` wraps the repository call, raises `LookupError` if the plan doesn't exist for that owner.
5. `app/modules/plans/presentation/router.py`: `POST /plans/{plan_id}/attachment` using `UploadFile` + `save_upload`.
6. `app/modules/me/infrastructure/mongo_me_repository.py#get_active_plan`: include the two fields in the returned dict (endpoint already uses `response_model=dict | None`, no schema change needed there).
7. `tests/test_plans_service.py`: extend the fake repository + add `set_attachment` unit tests.

## Constraints

- No new storage abstraction — `app/core/storage.py#save_upload` is reused exactly as InBody uses it.
- `GET /me/plan/active` stays `response_model=dict | None`; no Pydantic schema needed there.
