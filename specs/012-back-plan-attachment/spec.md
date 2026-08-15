# Feature Specification: Plan Attachment

**Feature Branch**: `012-back-plan-attachment`
**Created**: 2026-08-15
**Status**: Draft
**Type**: Feature

## Objective

Nutritionists author the weekly meal plan as a free-form document (grid of 7 days x meal slots with dish text, branding, signature, "próxima cita" line) in an external tool and export it as a PDF — not as structured `qty/unit` rows. `plans` had no way to carry that artifact. Same pattern already solved for InBody reports (`body_compositions.attachment_url`/`attachment_type` + `app/core/storage.py#save_upload`); this reuses it for `plans`.

## In Scope

- `plans` documents gain `attachment_url`/`attachment_type` (nullable).
- `PlanOut` schema exposes both fields.
- `POST /plans/{plan_id}/attachment` (multipart, owner-scoped): uploads via `save_upload(file, subfolder=f"plans/{plan_id}")`, sets the fields, returns the updated `PlanOut`.
- `GET /me/plan/active` (`mongo_me_repository.get_active_plan`) includes both fields so the patient-facing endpoint can surface them.
- `MongoPlansRepository.set_attachment_for_owner` / `PlansService.set_attachment`.

## Out of Scope

- Any pro-facing UI to upload the file (no nutritionist app exists yet; set via this API directly, same as InBody scans this session).
- Validating/parsing PDF contents — it's stored and served as-is, same as InBody.

## Baseline Behavior

- `plans` had no attachment concept; `GET /me/plan/active` only returned structured fields.

## Target Design

- Mirrors `body_compositions`: `save_upload` under `plans/{plan_id}`, served from the existing `/uploads` static mount, no new storage abstraction.

## Documentation Impact

- **Module docs to create/update**: `docs/architecture/ARCHITECTURE_GUARDRAILS.md` (none needed — no boundary change), `specs/SPEC_ROADMAP.md`.

## Acceptance Criteria

1. Given an owner and an existing plan, when `POST /plans/{plan_id}/attachment` is called with a PDF file, then the response's `attachment_url`/`attachment_type` are set and the file is fetchable at `attachment_url`.
2. Given a patient with that plan assigned, when `GET /me/plan/active` is called, then the response includes the same `attachment_url`/`attachment_type`.
3. Given a `plan_id` that doesn't belong to the caller's owner, when the attachment endpoint is called, then it 404s.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`
- Manual: uploaded the real PDF via the endpoint against the running dev backend and confirmed `GET /me/plan/active` for the test patient returns it, and the `/uploads/...` URL serves the file (200, `application/pdf`).
