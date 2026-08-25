# Feature Specification: Plan Meal Item Cooking State

**Feature Branch**: `037-back-plan-item-cooking-state`
**Created**: 2026-08-24
**Status**: Draft
**Type**: Feature

## Objective

A nutritionist writing "150 g de pechuga de pollo" usually means cooked weight, but a patient shopping/prepping needs the raw weight to buy and portion correctly (cooked chicken breast is meaningfully lighter than raw — moisture loss during cooking). The user asked for the patient to see both weights. This makes that distinction — and the other weight — real, optional, settable data instead of ambiguous.

## In Scope

- `PlanMealItem` gains `cooking_state: Optional[Literal['raw', 'cooked']] = None` and `equivalent_qty: Optional[float] = None` in `app/schemas/plan.py`.
- `equivalent_qty` is understood to be in the same `unit` as `qty`, representing the *other* state's weight (if `cooking_state == 'cooked'`, `equivalent_qty` is the raw weight, and vice versa) — not a separate unit or a computed conversion.

## Out of Scope

- No automatic raw↔cooked conversion ratio computed by the backend (e.g. "chicken loses 25% weight when cooked") — both values are always hand-entered by the nutritionist, since the actual ratio depends on the food and cooking method.
- No validation that `equivalent_qty` is "reasonable" relative to `qty` (e.g. no sanity-check that cooked < raw) — trusts nutritionist input, same posture as every other optional numeric field on this model.

## Baseline Behavior

`PlanMealItem` had no concept of raw vs. cooked weight at all — `qty`/`unit` was a single ambiguous number, and a patient had no way to know whether "150 g" meant before or after cooking.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: enables `nutri_pro` (meal-item cooking-state editor) and `nutri_app` (showing both weights) — both separate specs, shipped alongside this one.

## Acceptance Criteria

1. Given a `POST /plans` payload with an item carrying `cooking_state: "cooked"` and `equivalent_qty: 200`, when created, then `GET /plans/{id}` returns those same values unchanged.
2. Given an item that omits both fields, then they come back `null` — matching every existing plan's behavior today.
3. Given a pre-existing Mongo plan document with items that have neither key, then it still validates and returns `null` for both — no 500, no dropped items.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 124/124 green, no regressions.
- Live verification against the running backend: `POST /plans` with `cooking_state`/`equivalent_qty` set → `GET` unchanged; test plan deleted afterward.
- Backfilled the real, already-assigned patient plan's chicken and salmon items (150 g cooked / ~200 g and ~185 g raw respectively) and confirmed the round-trip through `PlanOut.model_validate()`.
