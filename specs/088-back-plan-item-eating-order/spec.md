# Feature Specification: Per-item eating-order on plan meals

**Feature Branch**: `feat/glucose-phase3`
**Created**: 2026-09-10
**Status**: Done — 325 unittests green
**Type**: Feature (tiny — one optional field)

## Objective

Glucose Phase 3: let the nutritionist **pin** a plan meal item to a course in
`nutri_app`'s "Orden sugerido" card, overriding the client-side auto-classifier.
Consumed by `nutri_pro` `117` (authoring) and `nutri_app` `078` (display).

## Data

`PlanMealItem` gains **`eating_order: Optional[int]`** — `Field(None, ge=1,
le=3)`: `1` = fibra/verduras (first), `2` = proteína/grasa, `3` =
carbohidratos (last). `None` = auto-classify. No migration; plan `meals` are
stored/served as verbatim dicts, so `PlanCreate`/`PlanUpdate`/`PlanOut` and the
patient's `GET /me/plan/active` carry it automatically — the only change is the
schema field + validation.

## Acceptance criteria

1. `PlanCreate` with `items[].eating_order` in 1..3 round-trips through
   `model_dump()` and out via `PlanOut`.
2. `eating_order = 4` (or 0) is a validation error.
3. Full unittest suite green.

## Docs

`specs/SPEC_ROADMAP.md` here. Cross-repo: `nutri_pro` `117`, `nutri_app` `078`.
