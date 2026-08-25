# Nutri Back Spec Roadmap

## Completed

- `001-vitta-architecture-bootstrap`
- `002-back-config-secrets-baseline`
- `003-back-auth-module-foundation`
- `004-back-appointments-module-foundation`
- `005-back-patients-module-foundation`
- `006-back-me-module-foundation`
- `007-back-plans-module-foundation`
- `008-back-test-foundation`
- `009-back-auth-registration-and-recovery`
- `010-back-me-profile-update`
- `011-back-grip-strength-metric`
- `012-back-plan-attachment`
- `013-back-plan-days-passthrough`
- `014-back-consultation-history-linkage`
- `015-back-appointments-patient-filter`
- `016-back-overlap-conflict-serialization-fix`
- `017-back-nutritionist-profile`
- `018-back-recipe-collections-owner-read`
- `019-back-body-compositions-list`
- `020-back-recipe-authoring`
- `021-back-food-diary`
- `022-back-recommendations`
- `023-back-plan-eating-out-options`
- `024-back-plan-assignment-history`
- `025-back-nutritionist-onboarding`
- `026-back-equivalencies-catalog`
- `027-back-consultations-foundation`
- `028-back-patient-account-linking`
- `029-back-invite-code-preview`
- `030-back-patient-self-registration`
- `031-back-hydration-tracking`
- `032-back-content-library`
- `033-back-consultation-requirement-menu`
- `034-back-nutritionist-content-library`
- `035-back-plan-meal-dish-name`
- `036-back-plan-item-macros`
- `037-back-plan-item-cooking-state`
- `038-back-usda-nutrition-lookup`
- `039-back-usda-food-portions`
- `040-back-tenant-isolation-hardening`
- `041-back-billing-foundation`
- `042-back-patient-nutritionist-chat`
- `043-back-progress-photos`
- `044-back-checkin-forms`
- `045-back-workout-plans`
- `046-back-branding-and-session-logging`

## Next Recommended Specs

- Live Stripe verification once a real Stripe account and test-mode API keys exist (`041-back-billing-foundation` shipped with `BILLING_PROVIDER=mock`; `StripeBillingProvider` is implemented but unverified against a live account).
- Numeric aggregation/trend-charting of check-in answers — deliberately out of scope for `044-back-checkin-forms`'s v1 (answers are stored as strings only).
- Numeric rollups over logged workout exercises (total volume, 1RM tracking) — deliberately out of scope for `045-back-workout-plans`'s v1.
- Session photos on a logged workout entry — deliberately deferred from `046-back-branding-and-session-logging`.
- A licensed exercise content/video database — `046`'s `exercise_library` is nutritionist-authored-and-reused only, by design; a real content-licensing relationship would be a separate, much larger initiative.
- `046-back-branding-and-session-logging` closes the real Phase 2 (dynamic per-tenant branding) that a prior session's numbering mix-up skipped, and deepens Phase 3 (training domain) with an exercise library and real logged session details — this now closes out the full TrainerStudio gap-analysis roadmap as originally scoped (Phase 0 multi-tenancy/billing, Phase 1 engagement, Phase 2 branding, Phase 3 training). Next natural step is user-driven: whatever real usage surfaces once nutritionists start using these features live.
