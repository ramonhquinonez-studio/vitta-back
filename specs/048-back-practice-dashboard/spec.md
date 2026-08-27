# Feature Specification: Practice-Wide Analytics Dashboard

**Feature Branch**: `048-back-practice-dashboard`
**Created**: 2026-08-25
**Status**: Draft
**Type**: Feature

## Objective

Closes the one real gap in an otherwise-covered "Analytics & Reporting" category from the "Vitta vs. TrainerStudio" parity report: `patient_detail_page.dart` already gives a nutritionist a per-patient overview, but there was no cross-patient, practice-wide view — no way to see total/new/active patient counts, upcoming/completed appointments, estimated revenue, or which patients have gone quiet, without opening each patient one at a time.

## In Scope

- `patients` module: new `GET /patients/dashboard` (nutritionist-only, already gated at router level), aggregating across all of the caller's own patients:
  - `total_patients`, `new_patients_this_month` (by `Patient.created_at`, newly added this spec).
  - `upcoming_appointments_this_week` (`status` in `confirmed`/`pending`, `start` in the next 7 days).
  - `completed_appointments_this_month` (`status="completed"`, `start` within the current calendar month).
  - `estimated_revenue_this_month` = `completed_appointments_this_month × nutritionist's own session_price` (0 when unset).
  - `active_patients` / `inactive_patients` — a patient counts as active if they have any measurement, food-diary entry, check-in response, workout log, or appointment (past *or* future — an upcoming booking is itself a sign of engagement) within the last 14 days; everyone else is returned by name as a "needs attention" list.
- `Patient` entity gains `created_at`. Already set by the two auth-flow patient-creation paths (invite claim, self-registration) — only `create_for_owner` (nutritionist adding a chart directly) was missing it, now fixed. Pre-existing patients keep `created_at=None` (not backfilled).
- New index on `checkin_responses` (`patient_id`, `submitted_at`) — didn't exist before this spec — plus `patients` (`owner_id`, `created_at`).

## Out of Scope

- No Mongo aggregation pipeline (`$group`/`$facet`) — the codebase has never used one (only `$lookup` exists, in `appointments`); the dashboard is built the same way as every other read in this module, as a sequence of plain `count_documents`/`find`/`distinct` calls.
- No exact "days since last activity" per inactive patient — just a yes/no signal (name only), keeping the query set to 5 simple `distinct` calls instead of a per-patient last-activity computation.
- No `created_at` backfill for patients created before this spec shipped.

## Baseline Behavior

No aggregate/practice-wide view existed. `Patient` had no `created_at` field on the one creation path that lacked it (`PatientsRepository.create_for_owner`).

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro` spec `046-front-practice-dashboard`.

## Acceptance Criteria

1. Given a nutritionist with patients, appointments, and logged activity, when they call `GET /patients/dashboard`, then every count matches what's actually in the database for their own patients only.
2. Given a patient has zero activity in any tracked collection for 14+ days, then they appear in `inactive_patients`; given they have even an upcoming appointment, they don't.
3. Given another nutritionist calls the same endpoint, then they see only their own data — zero counts if they have no patients.
4. Given `session_price` was never configured, then `estimated_revenue_this_month` is `0`, not an error.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 207/207 green (1 new `test_patients_service.py` case — a thin pass-through test; the real aggregation logic lives in the Mongo repository and isn't unit-testable without a live database in this codebase's established style, verified live instead).
- Live verification against the running backend: seeded 2 patients (one with a completed + an upcoming appointment, one with neither), a `session_price`, and confirmed every dashboard number matched exactly — including the inactive-patient flag and revenue calculation. Confirmed a second nutritionist's dashboard was all zeros (cross-tenant isolation). Test accounts/data cleaned up after.
