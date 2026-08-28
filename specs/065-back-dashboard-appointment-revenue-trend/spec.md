# Feature Specification: Dashboard Appointment & Revenue Trend

**Feature Branch**: `065-back-dashboard-appointment-revenue-trend`
**Created**: 2026-08-28
**Status**: Draft
**Type**: Feature

## Objective

Closes the last open item in `nutri_pro`'s "Charts/trend-lines on the practice dashboard" gap: `055-back-dashboard-patient-growth-trend` added the first trend line (new patients per month); "appointment/revenue trends still not built" was explicitly called out as remaining. Both close together — `estimated_revenue_this_month` already derives from `completed_appointments_this_month × session_price` (a self-declared number in the nutritionist's profile, not a real payment record — unrelated to `041-back-billing-foundation`'s Stripe integration), so a revenue-by-month trend is just that same multiplication applied per bucket.

## In Scope

- `completed_appointments_by_month` on `GET /patients/dashboard` — same 6-month bucket loop as `new_patients_by_month`, counting `appointments` with `status: "completed"` per month.
- `estimated_revenue_by_month` — derived in the router (matching where `estimated_revenue_this_month` is already derived) by multiplying each month's completed-appointment count by the nutritionist's `session_price`.

## Out of Scope

- No real payment/revenue records — this stays an estimate from session price × completed count, exactly like the existing "this month" figure. Actual revenue tracking would need real Stripe transaction data, gated on `041-back-billing-foundation`'s live-account item.

## Baseline Behavior

`get_dashboard` returned `new_patients_by_month` but nothing for appointments; the router computed `estimated_revenue_this_month` as a single number with no historical trend.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro`'s `076-front-dashboard-appointment-revenue-trend` consumes both new fields.

## Acceptance Criteria

1. Given a nutritionist has completed appointments across several of the last 6 months, then `completed_appointments_by_month` reflects the real per-month counts, oldest first.
2. Given the same data, `estimated_revenue_by_month` is each month's count × the nutritionist's current `session_price`.
3. Given no `session_price` is set, revenue amounts are 0, not an error — matches the existing `estimated_revenue_this_month` behavior.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 225/225 green (additive fields, no existing fixture broken — `test_get_dashboard_delegates_to_the_repository` doesn't assert on the specific keys added).
- Live verification against the running local server: `GET /patients/dashboard` returns both new fields with the correct shape (6 chronological month buckets each), confirmed against the seeded demo account.

## Documentation

- New `nutri_back/specs/065-back-dashboard-appointment-revenue-trend/{spec.md,plan.md,tasks.md}`, `SPEC_ROADMAP.md` append.
