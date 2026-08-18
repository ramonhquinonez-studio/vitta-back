# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`nutri_back` is the FastAPI backend for Vitta, a nutrition-coaching app connecting patients and nutritionists. It's consumed by a sibling Flutter client, `nutri_app`, at `../nutri_app` — a **separate git repository** (own history/remote), not a monorepo package.

## Commands

- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Configure: copy `.env.example` to `.env` and fill in `MONGO_URI`, `MONGO_DB`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, etc. (`docs/environments.md` has the full variable list and prod/staging rules)
- Run dev server: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- Full test suite: `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`
- Single test file: `PYTHONPATH=. .venv/bin/python -m unittest tests.test_appointments_service`
- Single test method: `PYTHONPATH=. .venv/bin/python -m unittest tests.test_appointments_service.<TestClass>.<test_method>`
- Seed dev data: `python app/scripts/seed_dev.py` (inspect it first — it writes to whatever DB `.env` currently points at)

## Architecture

### Module shape (mandatory for all new/refactored features)

Feature code lives in `app/modules/<feature>/` with hexagonal layers:
- `domain/` — entities and `Protocol`-based repository contracts; **zero FastAPI/Motor/framework imports**
- `application/` — use-case orchestration (services), depends only on `domain`
- `infrastructure/` — Mongo repositories and external adapters (e.g. Google Calendar) implementing the `domain` Protocols
- `presentation/` — the `APIRouter`, request/response Pydantic models, HTTP-only concerns

Dependency direction: `presentation -> application -> domain <- infrastructure`. `domain` never imports outward.

Migrated so far: `auth`, `appointments`, `patients`, `me`, `plans`, `nutritionist_profile`, `recipes`, `recommendations`. Their legacy `app/routers/<name>.py` files are now pinned to a single line — `from app.modules.<name>.presentation.router import router` — and `tests/test_router_wrapper_guardrails.py` fails the build if that line drifts. Never add logic back into these wrapper files.

Not yet migrated (still real logic in `app/routers/`): `devices.py`, `google_oauth.py`, `health.py`, `users.py`. New modules must be born in `app/modules/`, never in `app/routers/` (`docs/architecture/ARCHITECTURE_GUARDRAILS.md`, "Rule In Force").

### Cross-cutting (`app/core`, `app/db`)

- `app/core/config.py` — `Settings` (pydantic-settings), reads `.env`. `validate_security_baseline` **raises** if `JWT_SECRET`/`JWT_REFRESH_SECRET` are still dev placeholders while `APP_ENV` is `prod`/`production`/`staging`. `CORS_ORIGINS`/`GOOGLE_SCOPES` accept JSON or CSV.
- `app/core/security.py` — JWT create/decode (access + refresh) and password hashing.
- `app/core/deps.py` — `get_db()` (re-exports `app/db/mongo.get_db`) and `get_current_user` (Bearer-token dependency; looks up `db.users` by JWT `sub`, returns a plain dict). Standard `Depends(...)` used across routers.
- `app/db/mongo.py` — module-level Motor client/db, populated by `app/main.py`'s lifespan (`connect_to_mongo`). `get_db()` raises `RuntimeError` if called before startup — matters for scripts/tests that touch DB code outside the FastAPI lifespan.
- `app/db/init_indexes.py` — Mongo indexes created on startup; update when a module's Mongo schema changes.
- `app/core/scheduler.py` + `app/jobs/appointment_reminders.py` — APScheduler job (runs every minute) sending appointment reminders, registered in `app/main.py`'s lifespan.
- `app/core/notify.py` — Firebase Admin init + push notification sending.
- `app/integrations/google_calendar.py` — Calendar sync used from the appointments module; failures are **intentionally swallowed** so Calendar problems never break the core booking flow. Preserve the `no_sync` flag pattern already used on appointment endpoints.

### Auth flow

JWT access + refresh tokens issued by `AuthService` (`app/modules/auth/application/auth_service.py`). Clients send `Authorization: Bearer <access_token>`; `get_current_user` decodes it and loads the user. `POST /auth/refresh` mints a new pair from a valid refresh token. `nutri_app`'s `lib/core/network/api_client.dart` interceptor depends on this exact contract for its 401-retry flow — don't change the token payload shape (`sub`, `role`) or the `/auth/refresh` request/response shape without updating the frontend too.

## Spec-driven development (SDD) — mandatory workflow

Enforced by `docs/SDD_DOCUMENTATION_POLICY.md`. Before any feature, bugfix, refactor, API contract change, security/auth change, external-integration change, or architecture change counts as done:

1. Create/update `specs/<NNN-back-slug>/{spec.md,plan.md,tasks.md}` — `.specify/templates/refactor-spec-template.md` is the template shape; `specs/001-vitta-architecture-bootstrap/spec.md` is a filled example.
2. Update `docs/modules/architecture.md` (current migration status/gaps) and/or `docs/architecture/ARCHITECTURE_GUARDRAILS.md` if the change affects layering rules.
3. No secrets in code; no direct DB access from new/refactored `presentation` code — that belongs in `infrastructure`.

Doc hierarchy when sources conflict (`docs/README.md`): `docs/modules/*.md` > `docs/architecture/ARCHITECTURE_GUARDRAILS.md` > `docs/SDD_DOCUMENTATION_POLICY.md` > `specs/<id>/` > `README.md`.

## Secrets

`.env` and `firebase-service-account.json` are gitignored — never read, print, or commit either. `.env.example` documents every variable; `docs/environments.md` documents which are mandatory outside local dev.

## Frontend integration (`../nutri_app`)

Same SDD discipline and a parallel migration (fat handlers -> layered modules), mirrored in `nutri_app`'s own `CLAUDE.md`. An API contract change here (new field, renamed route, changed status code) usually needs a matching change in `nutri_app`'s `data/datasources` + `data/models` for the consuming module — check there before treating a backend-only change as complete.
