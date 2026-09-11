# Feature Specification: Left/right circumference sites

**Feature Branch**: `feat/body-figure-phase4`
**Created**: 2026-09-10
**Status**: Done — 328 unittests green
**Type**: Feature (tiny — vocabulary expansion)

## Objective

Body-figure Phase 4: let the paired limbs (arm/thigh/calf) be measured per
side. Consumed by `nutri_pro` `116` + `nutri_app` `077`.

## Data

`CIRCUMFERENCE_SITES` gains `arm_left`/`arm_right`/`thigh_left`/`thigh_right`/
`calf_left`/`calf_right`. The bare `arm`/`thigh`/`calf` keys stay valid and
mean "single value / side unspecified" (legacy data keeps rendering). No
migration. `circumference_goals` (spec 085) shares the vocabulary, so per-side
targets work automatically — and a client may fall back to the base site's goal
for a sided reading.

## Acceptance criteria

1. `POST /me/body-measurements` / `POST /patients/{id}/measurements` accept
   `arm_left` etc.; `waist_left` (an unpaired site) is a 400.
2. `PATCH /patients/{id}` accepts `circumference_goals: {"thigh_left": 55}`.
3. Full unittest suite green.

## Docs

`specs/SPEC_ROADMAP.md` here. Cross-repo: `nutri_pro` `116`, `nutri_app` `077`.
