# Implementation Plan: Plan Days Passthrough + Real Weekly Plan Data

**Branch**: `013-back-plan-days-passthrough` | **Date**: 2026-08-15 | **Spec**: `specs/013-back-plan-days-passthrough/spec.md`

## Summary

One-line bugfix (missing `days` passthrough) plus a data script that gives one patient's assigned plan real per-day content instead of the synthetic rotation.

## Steps

1. `mongo_me_repository.py#get_active_plan`: add `"days": plan.get("days", [])` next to the existing `meals`/`attachment_url` fields.
2. `app/scripts/seed_ramon_real_plan.py`: transcribe the real PDF into `RECIPES` (25 entries: 18 dishes + 7 deduplicated snack combos) and `DAYS` (7 × 5 meal tuples), then:
   - upsert a `recipe_collections` document ("Plan semanal de Ramón") with the 25 recipes;
   - `$set` the plan document's `days` field with the 7-day structure, referencing the new recipe ids.
3. Manual verification against the live dev Mongo/backend (no automated integration test harness exists for Mongo repositories in this codebase — consistent with how `attachment_url` was verified in `012-back-plan-attachment`).

## Constraints

- Script is idempotent for the recipe collection (`update_one` with `upsert=True` keyed on `owner_id`+`title`) but re-running regenerates fresh recipe ids each time (items in the plan doc are overwritten with the new ids in the same run, so consistency holds within one run — re-running twice is safe but wasteful, not harmful).
