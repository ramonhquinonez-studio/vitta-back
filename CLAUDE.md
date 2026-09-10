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

**Patient self-logged progress (`/me/measurements`) — spec `083`**: the patient doc carries `progress_log_enabled: bool` (missing == enabled). `PatientUpdate`/`PatientOut` expose it (owner-scoped `PATCH /patients/{id}`); `GET /me/profile` surfaces `patient.progress_log_enabled`; `POST /me/measurements` → **403** (`PermissionError`) when it's `False` (history `GET` unaffected); `PATCH /me/profile` **strips** the key so a patient can't re-enable their own. Cross-repo: `nutri_pro` `112` (the toggle), `nutri_app` `070` (hides the "Registrar" affordance).

Migrated so far: `auth`, `appointments`, `patients`, `me`, `plans`, `nutritionist_profile`, `recipes`, `recommendations`, `equivalencies`, `consultations` (and later `billing`, `messaging`, `checkin`, `workout_plans`, `exercise_library`, `eating_out_options`, `places_lookup`, plus `payments` / `payment_methods` / `stripe_webhooks` from spec `077`). Their legacy `app/routers/<name>.py` files are now pinned to a single line — `from app.modules.<name>.presentation.router import router` — and `tests/test_router_wrapper_guardrails.py` fails the build if that line drifts. Never add logic back into these wrapper files.

Not yet migrated (still real logic in `app/routers/`): `devices.py`, `google_oauth.py`, `health.py`, `users.py`. New modules must be born in `app/modules/`, never in `app/routers/` (`docs/architecture/ARCHITECTURE_GUARDRAILS.md`, "Rule In Force").

**Payments (Stripe native-SDK rails — specs `077`+`078`+`079`, modeled on `fidelity_back`; all built, live verification pending a real account)**:
- **`077` — `payments`** (one Stripe Customer per user id → `stripe_customers`; ephemeral keys; `POST /billing/setup-intent`; `stripe_error_to_http`), **`payment_methods`** (saved cards — Stripe is the source of truth, no local mirror — `GET/POST/PATCH/DELETE /billing/payment-methods`), **`stripe_webhooks`** (`POST /stripe/webhook`, one idempotent dispatcher via `stripe_webhook_events`; other modules add handlers with `register_handler`, wired from `app/main.py`).
- **`078` — subscription native sheet**: `StripeSubscriptionsService` (separate from `BillingService`), `POST /billing/subscription-sheet` (Subscription `default_incomplete` → first invoice's PaymentIntent client secret) + `POST /billing/subscription/verify` + `subscription_webhook_handlers.py`. `POST /billing/checkout` redirect kept as the web fallback.
- **`079` — patient → nutritionist via Connect**: `stripe_connect_accounts` collection, `payments` ledger, `ConnectService` + `ConsultationChargesService` (destination charges, `application_fee_amount` = `PLATFORM_FEE_BPS`), routes under `/payments/*`, `connect_webhook_handlers.py`. Payment state lives in the `payments` ledger (no `Consultation` field); price = `nutritionist_profile.session_price`. `GET /payments/received` resolves `patient_name` in the router (charges service stays free of the patients module).

**Booking protection (spec `080`, multi-phase, cross-repo — `nutri_pro` `111`, `nutri_app` `068`; partially supersedes drafted `nutri_app` `067`)**:
- **`080` Phase 1 (built, no money, no Stripe)** — `booking_policy` module: `BookingPolicy` per `owner_id` in `booking_policies` (`payment_mode` none/deposit/full, deposit %/fixed, `requires_approval`, `reschedule_limit`/`reschedule_notice_hours`, `cancellation_cutoff_hours`, `slot_hold_minutes`, optional `policy_text`). `GET`/`PUT /booking-policy/me` (nutritionist, resolved preview). `BookingPolicyService.resolve_for_patient` → `amount_due_cents` + auto Spanish `policy_text`. `MeService` gained an optional `booking_policy_service`; `GET /me/nutritionist_profile` embeds `booking_policy`, `GET /me/booking-policy` is the thin read, and `POST /me/appointments` rejects (400) without `policy_accepted` when the policy `needs_consent`, snapshotting the resolved terms + `policy_accepted_at` onto the appointment (immutable dispute record).
- User decisions: per-nutritionist approval toggle · deposit is the default mode · within-policy refunds 100% (platform eats the Stripe fee) · forfeit keeps the platform's application fee · reschedule limit + slot-hold configurable.
- **Phases 2–5 (designed in `specs/080-*/spec.md`, not built)**: deposit destination-charge at booking + slot-hold sweeper + approval state machine; cancellation/reschedule enforcement (`cancellation-preview`, refund-vs-forfeit, `no-show`); deposit→balance credit; dispute-evidence export + reminders + analytics.

The `stripe` SDK is **always a constructor arg** (`get_stripe()` in prod, `FakeStripe` in `tests/_fakes/`), never imported inside a service. Webhook handler modules split into pure `apply_*(repo, obj)` (unit-tested) + `handle_*(obj)` wrappers that resolve the repo from `get_db()`. Everything 503s until `STRIPE_SECRET_KEY`/`_PUBLISHABLE_KEY`/`_WEBHOOK_SECRET` are all set (`settings.stripe_native_enabled`); `billing`'s `MockBillingProvider` + hosted-checkout redirect keep working regardless. Legacy `POST /billing/webhook` is deprecated for `/stripe/webhook`.

**`081`/`082` — real test-account wiring (SDK v15 / current API):** the live `stripe` v15 `StripeObject` **rejects `.get()`** (it's not a `dict` subclass, unlike `FakeStripe._Obj`). Every SDK response read with `.get()` must first pass through **`stripe_client.as_dict(obj)`** (recursive `to_dict()` normalizer) — applied in the subscriptions service, `webhook_dispatcher.verify()`, connect + consultation-charges services, and (`082`, found on the first emulator run) `payment_methods_service`. **When adding any new `self._stripe.X.list()/retrieve()/create()` call whose result you read with `.get()`, wrap it in `as_dict()`.** Attribute access (`obj.id`) is fine and needs no wrapping. Also: the current Stripe API put the subscription's confirmable client secret on **`latest_invoice.confirmation_secret.client_secret`** (not `invoice.payment_intent`); `start_subscription_sheet` expands + reads both. `STRIPE_PRICE_PRO` is a `Settings` field (recurring Price id for the Pro plan, read by `seed_billing_plans.py`). Consultation `refund` (079) uses `reverse_transfer=True, refund_application_fee=True` — a full unwind of the destination charge (a plain refund would pay the patient from the platform balance and leave the nutritionist's cut + the platform fee in place). Test keys are currently **borrowed from `fidelity_back` (test mode)** and Connect is enabled there; the demo nutritionist's `stripe_connect_accounts` row points at a `type=custom` chargeable test account so the charge path works without hosted onboarding. Subscription + full Connect consultation charge/verify/refund flows are **live-verified in test mode** (see `081`); a dedicated Vitta account + deployed backend remain for production.

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
