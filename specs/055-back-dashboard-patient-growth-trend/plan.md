# Implementation Plan: Practice Dashboard Patient Growth Trend

**Branch**: `055-back-dashboard-patient-growth-trend` | **Date**: 2026-08-26 | **Spec**: `specs/055-back-dashboard-patient-growth-trend/spec.md`

## Summary

A new month-bucketed computation appended to `MongoPatientsRepository.get_dashboard`'s returned dict — `PatientsService.get_dashboard` and the router already pass this dict through unchanged, so neither needs editing.

## Steps

1. `app/modules/patients/infrastructure/mongo_patients_repository.py`: new module-level `_add_months(date: datetime, months: int) -> datetime` (stdlib-only month-boundary walker). `get_dashboard` computes `new_patients_by_month` — starting from `_add_months(start_of_month, -5)`, 6 sequential `count_documents({"owner_id":..., "archived_at": None, "created_at": {"$gte": bucket_start, "$lt": bucket_end}})` calls, each appended as `{"month": bucket_start.strftime("%Y-%m"), "count": count}`, added to the returned dict.

## Constraints

- No schema/router/service changes — both already forward the repository's dict as-is (`app/modules/patients/presentation/router.py`'s `get_practice_dashboard` only adds `estimated_revenue_this_month`/`revenue_currency` on top).
- No new dependency — plain stdlib `datetime` arithmetic, matching this file's existing style (no aggregation pipeline usage anywhere in `get_dashboard`).
