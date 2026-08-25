# Tasks: Billing Foundation (Subscription Plans & Quota)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `billing/domain`: entidades + Protocols (`BillingRepository`, `BillingProviderRepository`).
- [x] T003 `billing/infrastructure`: `MongoBillingRepository`, `MockBillingProvider`, `StripeBillingProvider`.
- [x] T004 `billing/application/billing_service.py`.
- [x] T005 `schemas/billing.py` + `billing/presentation/router.py` (5 endpoints + 2 mock-only).
- [x] T006 `config.py`: settings de Stripe/proveedor.
- [x] T007 `app/core/quota.py`: `PatientQuotaCheckerAdapter`.
- [x] T008 `patients`: `count_for_owner`, `PatientQuotaChecker`, wiring en `create_patient`/`claim_patient`.
- [x] T009 `auth`: `PatientQuotaChecker`, wiring en `register()` (solo invites que crean paciente nuevo).
- [x] T010 Wiring de routers (`patients`, `auth`, `billing`) + mapeo `PermissionError` → 402.
- [x] T011 Auto-enroll del plan por defecto en `register_nutritionist`.
- [x] T012 `app/scripts/seed_billing_plans.py`.
- [x] T013 Tests: `test_billing_service.py` (9 casos), `test_patients_service.py` (+2), `test_auth_service.py` (+2).
- [x] T016 `BillingService._effective_plan`: fallback al plan por defecto cuando `status` no es `active`/`trialing`; `GET /billing/mock-cancel` para poder ejercitarlo sin Stripe real.
- [x] T017 Tests nuevos para el fallback por estado (4 casos en `test_billing_service.py`).

## Phase 3: Validation

- [x] T014 Suite completa → 150/150 verde.
- [x] T015 Verificación en vivo end-to-end en modo mock (registro → plan gratis automático → límite de 3 → 402 → checkout mock → upgrade a Pro → límite de 50 → portal mock).
- [x] T018 Verificación en vivo del fallback por estado: upgrade a Pro → 4 pacientes → cancelar (mock-cancel) → 5to paciente 402 (cae a límite gratis) → re-checkout Pro → 5to paciente 201 (límite restaurado).

## Evidence

- Suite completa: 150/150 verde.
- Verificación en vivo: ambos flujos (alta/upgrade y cancelación/reactivación) confirmados contra el backend real corriendo localmente, datos de prueba limpiados al final.
