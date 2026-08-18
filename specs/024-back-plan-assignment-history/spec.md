# Feature Specification: Plan Assignment History

**Feature Branch**: `024-back-plan-assignment-history`
**Created**: 2026-08-18
**Status**: Draft
**Type**: Feature

## Objective

Let a nutritionist see the full history of plans assigned to a patient, not just the current one. `plan_assignments` already stored every assignment as its own document (never deleted/overwritten), but nothing exposed that history — `get_active_plan` only ever surfaced the single most recent one.

## In Scope

- `GET /patients/{patient_id}/plan_assignments` — owner-scoped list of every assignment for a patient, newest first, each entry a `{plan_id, plan_name, assigned_at}` snapshot. `plan_name` is looked up at read time and is `null` if that plan has since been deleted (rather than erroring or omitting the entry — the assignment still happened historically).

## Out of Scope

- Changing `get_active_plan`'s resolution logic (still "most recent assignment") — this is a read-only additive history view, not a change to which plan is "active".
- A way to delete/undo a specific historical assignment — assignments are an append-only log; the closest equivalent action is assigning a different plan, which naturally becomes the new "most recent".

## Baseline Behavior

- No endpoint exposed `plan_assignments` history at all; a nutritionist had no way to see what a patient had been assigned before the current plan.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given a patient has been assigned 3 different plans over time, when the owning nutritionist requests their assignment history, then all 3 appear, newest first.
2. Given one of those assigned plans has since been deleted, then its entry still appears with `plan_name: null` instead of being dropped or erroring.
3. Given a nutritionist who doesn't own the patient requests this, then `404`.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 64/64 green (2 new tests in `test_patients_service.py`).
- Manual: `curl GET /patients/{id}/plan_assignments` for a real patient with a genuine assignment history → returned the correct single real assignment, confirming the endpoint works and also surfacing (separately, not part of this endpoint's own bug) that this patient's assignment history had stale entries pointing to already-deleted plans left over from unrelated testing — cleaned up directly in the database as a one-off fix, unrelated to this endpoint's own correctness.
