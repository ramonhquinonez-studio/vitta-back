# Feature Specification: Practice Dashboard Patient Growth Trend

**Feature Branch**: `055-back-dashboard-patient-growth-trend`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

Explicitly flagged in `SPEC_ROADMAP.md`: "Charts/trend-lines on the practice dashboard — `048-back-practice-dashboard` shows current-state counts only, matching the backend's own scope." This adds the first trend: new patients per month, last 6 months.

## In Scope

- `GET /patients/dashboard` gains a `new_patients_by_month` field: 6 entries, chronological (oldest→newest, current month last), each `{"month": "YYYY-MM", "count": N}`.

## Out of Scope

- No other trend lines (appointments, revenue) — one clear, contained win at a time.
- No aggregation pipeline — matches the existing `get_dashboard`'s simple `count_documents`-per-bucket style.
- Same undercounting caveat `new_patients_this_month` already has: patients created before `048-back-practice-dashboard` shipped have `created_at = None` and are invisible to any month bucket.

## Baseline Behavior

`get_dashboard` returned only current-state counts (`total_patients`, `new_patients_this_month`, etc.) — no historical breakdown.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` spec `059-front-dashboard-patient-growth-trend` consumes this.

## Acceptance Criteria

1. Given a nutritionist hits `GET /patients/dashboard`, then `new_patients_by_month` contains exactly 6 entries in chronological order.
2. Given a patient was created this month, then the last entry's `count` matches `new_patients_this_month`.

## Validation

- Full backend unittest suite green (no test file changes — the service/router are pure passthroughs, unchanged; the new computation lives entirely in the Mongo repository, verified live instead of via the fake-repository service tests).
- Live-curl verification: created 2 patients for a throwaway nutritionist, confirmed `new_patients_by_month` returned 6 chronological entries with the current month's count (2) matching `new_patients_this_month`. Cleaned up afterward.
