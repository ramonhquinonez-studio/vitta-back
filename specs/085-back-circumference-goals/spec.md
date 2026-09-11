# Feature Specification: Per-site circumference goals

**Feature Branch**: `feat/circumference-goals`
**Created**: 2026-09-10
**Status**: Done — 319 unittests green
**Type**: Feature (small — one field on `Patient`)

## Objective

Back the body-figure Phase 3 goals feature (`nutri_app` `074`, `nutri_pro`
`114`): let the nutritionist set a target circumference (cm) per site so both
apps can colour the figure by **distance to goal** instead of only trend, and
show the patient how far they are from each target.

## Data

`patients` documents gain **`circumference_goals: dict[str, float]`** — cm per
site, keyed by the same `CIRCUMFERENCE_SITES` vocabulary as
`measurements.circumferences` (`neck, chest, arm, waist, hip, thigh, calf`).
Missing == no goal. No migration (default `{}`).

## API

- **`PATCH /patients/{id}`** (`PatientUpdate.circumference_goals`, nutritionist,
  owner-scoped) — sets the goal map. `{}` clears every goal; a partial map
  replaces the whole map (send the full desired set). Validated against the site
  vocabulary and `0 < cm <= 300` (shared `_clean_circumference_goals`).
- **`GET /patients/{id}`** — `PatientOut.circumference_goals` (default `{}`).
- **`GET /me/profile`** — the `patient` block now carries `circumference_goals`
  so the patient app can read its own targets.
- **`PATCH /me/profile`** strips `circumference_goals` (nutritionist-only, same
  as `progress_log_enabled` in spec 083).

## Out of scope

- L/R per-limb values and a front/back figure toggle — body-figure Phase 4.
- Any goal-progress history/analytics beyond "latest reading vs. goal".

## Acceptance criteria

1. `PATCH /patients/{id}` with `circumference_goals: {"waist": 78}` persists and
   is returned by `GET /patients/{id}` and `GET /me/profile`.
2. `circumference_goals: {}` clears them.
3. An unknown site or an out-of-range cm → 400.
4. `PATCH /me/profile` cannot set them.
5. Full unittest suite green.

## Docs

`CLAUDE.md` is `nutri_pro`/`nutri_app`-side; `specs/SPEC_ROADMAP.md` here.
Cross-repo: `nutri_pro` `114`, `nutri_app` `074`.
