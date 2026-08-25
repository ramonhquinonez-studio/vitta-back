# Feature Specification: Billing Foundation (Subscription Plans & Quota)

**Feature Branch**: `041-back-billing-foundation`
**Created**: 2026-08-24
**Status**: Draft
**Type**: Feature

## Objective

Vitta's self-serve nutritionist signup and `owner_id`-based tenant isolation already exist (confirmed by codebase audit, hardened in `040-back-tenant-isolation-hardening`) — what's missing to reach a TrainerStudio-style multi-tenant SaaS is billing: subscription tiers, a real payment integration, and enforcement of a plan's client limit. This builds that from scratch as a new `billing` module.

## In Scope

- New `billing` module: `SubscriptionPlan` (name, client limit, Stripe price id, default flag) and `Subscription` (owner, plan, status, provider ids) entities, Mongo-backed repository, and a swappable `BillingProviderRepository` — a `MockBillingProvider` (instant, no external account) for local dev, `StripeBillingProvider` for production, selected by `Settings.BILLING_PROVIDER`.
- `GET /billing/plans` (public), `GET /billing/subscription`, `POST /billing/checkout`, `POST /billing/portal` (all three nutritionist-only), `POST /billing/webhook` (Stripe-signature-verified, stripe-mode only).
- Every nutritionist is auto-enrolled in the default (free) plan the moment `POST /auth/register-nutritionist` succeeds — no null-subscription edge case anywhere downstream.
- Quota enforcement at every point a patient becomes owned by a nutritionist: `PatientsService.create_patient`, `PatientsService.claim_patient`, and — via a `PatientQuotaChecker` Protocol each module declares independently, composed by the router layer through `PatientQuotaCheckerAdapter` (`app/core/quota.py`) so neither `patients` nor `auth` imports `billing` directly — `AuthService.register`'s new-patient-via-invite-code path. All three surface a `402 Payment Required` when exceeded.
- `app/scripts/seed_billing_plans.py`: idempotent seed for the default free plan (3-patient limit).
- `BillingService._effective_plan`: a subscription whose status isn't `active`/`trialing` (i.e. `past_due`, `canceled`, anything else Stripe reports) falls back to the *default* plan's limit for quota purposes — `plan_id` itself is left untouched by `handle_webhook`, so reactivating restores the paid tier's real limit automatically, with no separate "restore" logic needed. `GET /billing/mock-cancel` (mock-mode only, linked from the mock portal page) lets this be exercised without a real Stripe account.

## Out of Scope

- No Tenant/Organization entity — a nutritionist's own `user_id` is the tenant/billing account. Revisit only if multi-nutritionist practices become a real requirement.
- No live Stripe verification in this pass — `StripeBillingProvider` is fully implemented but untested against a real account (none exists yet); `BILLING_PROVIDER` defaults to `"mock"`.
- No retroactive quota enforcement if a plan is *downgraded* to a lower tier while over its new limit — existing patients aren't removed or archived; only *new* ones are blocked. Deliberately left as a product decision (which patients would be affected, and how, isn't obvious) rather than an engineering default.
- No proration, invoicing, dunning-email, or trial-period logic — `Subscription.status` tracks what Stripe reports, nothing computed locally.

## Baseline Behavior

Zero billing/subscription/quota infrastructure existed in any of the three repos (confirmed by exhaustive grep). A nutritionist could add unlimited patients.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro` spec `039-front-billing` (the "Plan y facturación" screen and paywall UX). No `nutri_app` change — patients aren't billed.

## Acceptance Criteria

1. Given a freshly-registered nutritionist, when `GET /billing/subscription` is called, then it returns the default plan, auto-enrolled without a separate call.
2. Given a nutritionist at their plan's patient limit, when creating a new patient (directly, via invite-code redemption, or via claim), then it's refused with `402` and no patient/user record is left behind.
3. Given `BILLING_PROVIDER=mock`, when a nutritionist starts checkout for a higher-tier plan and the returned URL is opened, then the subscription updates immediately and the new limit takes effect.
4. Given a plan with `client_limit: None`, then quota is never enforced regardless of patient count.
5. Given a nutritionist on a paid plan whose subscription becomes `canceled` or `past_due`, when the free plan's limit is already met or exceeded, then further patient creation is refused with `402` even though the paid plan's own limit wouldn't be hit — and reactivating (status returns to `active`) immediately restores the paid plan's real limit.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 150/150 green (13 billing-service tests including 4 for status-aware quota fallback, 2 patients-quota tests, 2 auth-quota tests, on top of `040`'s hardening tests).
- Live, mock mode: registered a fresh nutritionist, confirmed auto-enrolled free plan (`GET /billing/subscription`); created 3 patients (limit), 4th refused `402`; started checkout for a seeded "Pro" (50-limit) plan, hit the returned `mock-confirm` URL, confirmed `GET /billing/subscription` now shows Pro and a 4th patient succeeds; confirmed `POST /billing/portal` returns a working mock URL. Separately: upgraded to Pro, created 4 patients, canceled via `/billing/mock-cancel`, confirmed `plan_id` stayed Pro but a 5th patient was refused `402` (fell back to the free limit of 3, already over with 4); re-checked-out Pro, confirmed the 5th patient then succeeded (limit restored). Test data cleaned up after both passes.
