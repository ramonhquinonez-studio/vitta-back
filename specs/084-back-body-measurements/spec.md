# Feature Specification: Body-measurement circumferences (interactive body figure)

**Feature Branch**: `feat/body-measurements-figure`
**Created**: 2026-09-10
**Status**: Done — 318 unittests green
**Type**: Feature (small)

## Objective

Back the interactive body-figure feature (`nutri_app` `072`, `nutri_pro` `113`):
store tape-measure circumferences per site alongside weight/photo entries, and
let both the patient and the nutritionist record them.

## Data

`measurements` documents gain **`circumferences: dict[str, float]`** (cm per
site). Sites are a fixed vocabulary — `CIRCUMFERENCE_SITES` in
`app/schemas/body_measurements.py`: `neck, chest, arm, waist, hip, thigh, calf`.
Missing == not measured. No migration (default `{}`).

## API

- **`POST /me/body-measurements`** (patient, JSON `BodyMeasurementsIn`) — creates
  a `measurements` doc (no photo). Respects the spec-083 `progress_log_enabled`
  gate → **403** when off. **400** when nothing is provided.
- **`POST /patients/{id}/measurements`** (nutritionist, owner-scoped) — records a
  circumference set (+ optional weight/fat/waist) for a patient.
- `GET /me/measurements` and `GET /patients/{id}/measurements` now include
  `circumferences` on every row.

Validation (`BodyMeasurementsIn`): unknown site → 422; each value `0 < cm <= 300`,
rounded to 0.1.

## Out of scope

- Left/right per-limb values (Phase 1 averages to one value client-side).
- Goal-per-site (the figure's colour coding is trend-based on the client).
- Any change to InBody / weight / photo flows.

## Acceptance criteria

1. `POST /me/body-measurements {"circumferences": {"waist": 82}}` → a row that
   `GET /me/measurements` returns with that map.
2. Same POST with `progress_log_enabled: false` → 403.
3. `POST /patients/{id}/measurements` by the owner → 201; by a non-owner → 404.
4. Empty payload → 400. Unknown site → 422.
5. `unittest` suite green.

## Docs

`CLAUDE.md` (patients/me modules), `specs/SPEC_ROADMAP.md`. Cross-repo:
`nutri_app` `072`, `nutri_pro` `113`.
