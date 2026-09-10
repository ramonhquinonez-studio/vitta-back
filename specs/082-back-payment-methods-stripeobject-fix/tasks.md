# Tasks: Payment-methods StripeObject fix + on-device verification

- [x] T1 — `payment_methods_service.py`: `as_dict()` on `PaymentMethod.list` / `PaymentMethod.retrieve` / `Customer.retrieve` results in `list_cards`, `add_card`, `_assert_owned`.
- [x] T2 — `nutri_pro` + `nutri_app` `stripe_card_sheet.dart`: `SingleChildScrollView` so the sheet clears the keyboard.
- [x] T3 — `nutri_pro` `BillingController.currentPlan`: only an `active`/`trialing` subscription counts; else the default plan (+ test).
- [x] T4 — Full backend suite green (309); `nutri_pro`/`nutri_app` `flutter analyze` + `flutter test` green.
- [x] T5 — Roadmap + `CLAUDE.md` (`081`/`082` note) + `nutri_pro` `109` spec follow-up.
- [x] T6 — `nutri_app` "Pagar consulta" 404: `consultation_charges_router` resolver falls back to `MongoAppointmentsRepository.get_for_owner` (nutri_app's "Historial de consultas" lists appointments, not consultations); `PatientPaymentsController` surfaces the backend `detail` + stays silent on user-cancel. Verified live (`sheet` → 200 for `patient_demo`).
- [ ] T7 — Human-driven final step: type `4242 4242 4242 4242` in the card sheet + Pagar (subscription on Android emulator; "Pagar consulta" on iOS simulator, logged in as `patient_demo@nutri.app`). Stripe's Android `CardNumberEditText` ignores adb synthetic input; the iOS simulator keyboard works.
