# Feature Specification: Production-Readiness Hardening

**Feature Branch**: `066-back-production-readiness-hardening`
**Created**: 2026-08-28
**Status**: Draft
**Type**: Security/Hardening

## Objective

A dedicated pre-launch security/robustness audit (read-only research pass, then fixes) surfaced four concrete issues worth fixing before real traffic, plus stale architecture documentation. This closes all of them.

## In Scope

1. **Upload content-type spoofing** (`app/core/storage.py`): `save_upload` derived the saved file's extension from the client-supplied `filename` before falling back to a content-type map. Since `/uploads` is served via `StaticFiles`, which infers response `Content-Type` from the extension, a client could upload arbitrary content named e.g. `x.html` and get it served back as `text/html` from the API's own origin — a stored-XSS vector. Fixed: extension is now derived *only* from the declared `content_type` (allowlist), never the filename; unrecognized content types fall back to `.bin` (served as `application/octet-stream`, never renderable).
2. **Missing upload size limits**: 5 of 8 `save_upload` call sites had no `max_size_bytes` at all (InBody scans, plan PDF attachments, progress photos, workout session photos, profile logos) — disk-exhaustion DoS risk from any authenticated user. All five now have a limit (15MB for photos, 25MB for PDFs/reports, 5MB for logos), each wrapped in a `try/except ValueError` → `413`.
3. **No rate limiting on `/auth/login` or `/auth/forgot-password`**: the `rate_limit()` dependency already existed and was applied to registration, but not to the two endpoints where brute-force/enumeration risk matters most. Now applied: login (20/hour/IP), forgot-password (5/hour/IP).
4. **CORS fails open**: if `CORS_ORIGINS` was left unset, `main.py` defaulted to `["*"]` with `allow_credentials=True` — CORSMiddleware handles this by echoing back any request's Origin header, functionally trusting any origin for credentialed requests. `config.py`'s `validate_security_baseline` now fails startup outside local dev if `CORS_ORIGINS` is empty, matching the existing JWT-secret placeholder check's fail-closed pattern.
5. **Messaging attachment upload had no ownership check**: `POST /patients/{patient_id}/messages/attachment` accepted any `patient_id` with no verification that it belonged to the requesting nutritionist before uploading — the only upload endpoint in the codebase missing this check (every other owner-scoped endpoint verifies first). Fixed: `MessagingService.ensure_patient_belongs_to_owner` is now checked before the upload proceeds, returning 404 for an unowned patient.
6. **Stale `docs/modules/architecture.md`**: claimed only 5 modules had migrated off fat routers; actually 17 of 21 have. Corrected, with the real remaining 4 (`users`, `devices`, `google_oauth`, `health`) listed explicitly as the actual remaining migration backlog.

## Out of Scope

- Migrating the 4 remaining fat routers themselves — a real but separate, larger effort (`google_oauth.py` alone is 130 lines), tracked in the corrected architecture doc, not bundled into this security pass.
- Structured logging — flagged by the audit as valuable for production debugging, but a broader, lower-urgency effort than the four concrete security items above; not addressed here.
- IDOR sweep beyond what the audit found — the audit did check `patients`/`messaging` modules specifically and found the codebase's ownership-scoping convention consistently applied elsewhere.

## Baseline Behavior

See each numbered item above for the specific pre-fix behavior.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`, `docs/modules/architecture.md` (already corrected as part of this spec).
- **Cross-repo impact**: none — backend-only.

## Acceptance Criteria

1. Uploading a file with a spoofed `.html`/`.exe`-style filename but a safe declared content-type is saved with the extension matching the content-type, never the filename.
2. Each of the 5 previously-unguarded upload endpoints rejects an over-limit file with `413`, not an unhandled `500`.
3. `/auth/login` and `/auth/forgot-password` return `429` after their respective per-IP thresholds within the hour window.
4. `Settings()` fails to construct when `APP_ENV` is `prod`/`production`/`staging` and `CORS_ORIGINS` is empty.
5. `POST /patients/{patient_id}/messages/attachment` returns `404` for a `patient_id` not owned by the requesting nutritionist, without ever calling `save_upload`.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 227/227 green (225 previous + 2 new `test_storage.py` regression tests for the content-type-spoofing fix).
- Live verification against the running local server: confirmed the ownership check returns 404 for an unowned/nonexistent patient id, and confirmed a file uploaded with filename `evil.html` + content-type `image/jpeg` is saved with a `.jpg` extension — both against the seeded demo account, cleaned up after.
