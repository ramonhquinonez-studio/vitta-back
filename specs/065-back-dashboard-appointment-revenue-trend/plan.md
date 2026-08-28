# Implementation Plan: Dashboard Appointment & Revenue Trend

**Feature Branch**: `065-back-dashboard-appointment-revenue-trend`

## Summary

Mirrors `new_patients_by_month`'s exact bucketing loop for appointments, then derives revenue from it in the router alongside the existing `estimated_revenue_this_month` computation.

## Steps

1. **`app/modules/patients/infrastructure/mongo_patients_repository.py`** `get_dashboard`: after the `new_patients_by_month` loop, an identical 6-month bucket loop counting `self._db.appointments.count_documents({"owner_id": owner_oid, "status": "completed", "start": {"$gte": bucket_start, "$lt": bucket_end}})`, appended as `completed_appointments_by_month` in the returned dict.
2. **`app/modules/patients/presentation/router.py`** `get_practice_dashboard`: after computing `session_price` and `estimated_revenue_this_month`, adds `dashboard["estimated_revenue_by_month"] = [{"month": b["month"], "amount": b["count"] * session_price} for b in dashboard["completed_appointments_by_month"]]`.

## Constraints

- No test fixture changes needed — the service-level test fakes the whole dashboard dict and doesn't assert on individual keys.
