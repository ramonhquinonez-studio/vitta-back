# Implementation Plan: Billing Foundation (Subscription Plans & Quota)

**Branch**: `041-back-billing-foundation` | **Date**: 2026-08-24 | **Spec**: `specs/041-back-billing-foundation/spec.md`

## Summary

A new `billing` module following the standard `domain/application/infrastructure/presentation` shape, plus a small dependency-inversion seam (`PatientQuotaChecker` Protocol, declared independently in `auth` and `patients`, composed by a shared adapter) so the two consuming modules never import `billing` directly.

## Steps

1. `billing/domain/entities.py`: `SubscriptionPlan`, `Subscription` dataclasses.
2. `billing/domain/repositories.py`: `BillingRepository` (plans + subscriptions, Mongo) and `BillingProviderRepository` (`create_checkout_session`, `create_portal_session`, `parse_webhook_event` — the swappable piece) Protocols.
3. `billing/infrastructure/mongo_billing_repository.py`: standard `_as_oid`-scoped CRUD.
4. `billing/infrastructure/mock_billing_provider.py`: returns a URL pointing back at this backend's own `/billing/mock-confirm`, which activates the subscription when hit — simulates a completed checkout with zero external dependency.
5. `billing/infrastructure/stripe_billing_provider.py`: real Stripe Checkout/Portal/webhook-verification calls (`stripe` SDK, lazy-imported so it's never required unless `BILLING_PROVIDER=stripe`).
6. `billing/application/billing_service.py`: `list_plans`, `get_my_subscription` (auto-enrolls the default plan if none exists yet — the actual mechanism behind "every nutritionist has a plan from day one"), `enroll_default_plan`, `start_checkout`, `open_portal`, `handle_webhook`, `check_patient_quota(owner_id, *, current_patient_count)`.
7. `app/schemas/billing.py` + `billing/presentation/router.py`: the 5 endpoints listed in the spec, plus `GET /billing/mock-confirm`/`GET /billing/mock-portal` (mock-mode-only, 404 otherwise).
8. `app/core/config.py`: `BILLING_PROVIDER`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY`.
9. `app/core/quota.py`: `PatientQuotaCheckerAdapter` — composes a `BillingService` with a `count_patients` callable into the `check(owner_id)` shape both `auth` and `patients` declare.
10. `patients/domain/repositories.py`: `count_for_owner` on `PatientsRepository`, `PatientQuotaChecker` Protocol; `infrastructure`: implementation; `application/patients_service.py`: `create_patient`/`claim_patient` call it first.
11. `auth/domain/repositories.py`: `PatientQuotaChecker` Protocol (independently declared, same shape); `application/auth_service.py`: checked once, before `create_user`, only when the invite has no `patient_id` (i.e. will create a *new* patient — linking an existing chart doesn't grow the roster and isn't gated).
12. Router wiring: `patients`/`auth`/`billing` routers' service-factory functions compose the adapter via `get_billing_service` (defined in `billing`'s router, imported by the other two); `PermissionError` → `402` in all three routers' relevant endpoints.
13. `auth` router's `register_nutritionist` endpoint calls `billing_service.enroll_default_plan(user.id)` right after successful registration.
14. `app/scripts/seed_billing_plans.py`: idempotent by `is_default: True` (not a fixed string id, since `_id` here is a real ObjectId).
15. Tests: `tests/test_billing_service.py` (fake repository + fake provider), extensions to `tests/test_patients_service.py` and `tests/test_auth_service.py` with a small `_FakeQuotaChecker`.

## Constraints

- Quota is checked *before* any user/patient record is created — a failed check must never leave an orphan account behind.
- The mock provider's "checkout URL" is same-backend and relative; a real Stripe URL is always absolute — the Flutter client resolves relative URLs against its own configured base URL, so this needs no server-side awareness of the client's origin.
