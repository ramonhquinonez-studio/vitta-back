# Feature Specification: Per-patient progress-log toggle

**Feature Branch**: `083-back-patient-progress-log-toggle`
**Created**: 2026-09-09
**Status**: Done (2026-09-09) — 313 unittests green. Cross-repo: `nutri_pro` `112`, `nutri_app` `070` both shipped.
**Type**: Feature (small — one field + one guard)

## Objective

Let a nutritionist turn a patient's **self-logged progress** (`/me/measurements` —
weight / % fat / waist / notes / photo) on or off per patient. Some coaches
deliberately don't want clients self-weighing between consultations; the
nutritionist's InBody / consultation measurements stay the authoritative record
regardless.

## Data

New patient-document field **`progress_log_enabled: bool`**, default **`True`**
(missing == enabled, so every existing patient keeps self-logging).

## API

- **`PATCH /patients/{id}`** (nutritionist, owner-scoped) — `PatientUpdate` gains
  `progress_log_enabled: bool | None`. `PatientOut` returns `progress_log_enabled`
  (defaults `True`).
- **`GET /patients/{id}`** — returns `progress_log_enabled`.
- **`GET /me/profile`** — `patient.progress_log_enabled` exposed so `nutri_app` can
  hide the "Registrar" affordance proactively.
- **`POST /me/measurements`** — returns **403** (`PermissionError` →
  `HTTPException(403, "Tu nutriólogo desactivó el registro de progreso.")`) when the
  patient's flag is `False`. `GET /me/measurements` is unaffected (history stays
  visible).
- **`PATCH /me/profile`** — `progress_log_enabled` is **stripped** from the patient's
  own update payload (a patient must not re-enable it themselves).

## Out of scope

- A "photos only, no scale" mode (single boolean for now).
- Migrating/backfilling existing docs (default handles it).
- Any change to InBody, consultations, check-ins, workout logs.

## Acceptance criteria

1. `PATCH /patients/{id}` with `{"progress_log_enabled": false}` → `GET` reflects it.
2. With the flag false, `POST /me/measurements` → 403; `GET /me/measurements` → 200.
3. `GET /me/profile` includes `patient.progress_log_enabled`.
4. `PATCH /me/profile {"progress_log_enabled": true}` on a disabled patient does **not**
   re-enable it.
5. A patient with no `progress_log_enabled` key can still POST measurements.
6. `unittest` suite green.

## Documentation impact

`CLAUDE.md` (patients module field list), `specs/SPEC_ROADMAP.md`. Cross-repo:
`nutri_pro` `112`, `nutri_app` `070`.
