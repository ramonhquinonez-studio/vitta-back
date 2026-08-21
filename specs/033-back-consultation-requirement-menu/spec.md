# Feature Specification: Consultation Requirement/Distribution/Menu

**Feature Branch**: `033-back-consultation-requirement-menu`
**Created**: 2026-08-20
**Status**: Draft
**Type**: Feature

## Objective

Phase 2 of the "Consultation as one continuous session" redesign, explicitly deferred by `027-back-consultations-foundation`'s "Out of Scope" and named in `specs/SPEC_ROADMAP.md`'s "Next Recommended Specs": give the consultation record three more autosaving sections — Requerimiento (energy-requirement inputs), Distribución (macro %-split target), and Menú (equivalency-exchange allocation) — so `nutri_pro`'s wizard can replace its `_PlaceholderStep()` for those three steps with the real calculator the nutritionist currently runs by hand in a spreadsheet.

## In Scope

- `Consultation` gains three more optional sections, mirroring `evaluation`'s existing shape exactly: `requirement: RequirementInput | None` (`wrist_cm`, `activity_factor`, `calorie_adjustment`), `distribution: DistributionInput | None` (`target_kcal`, `carbs_pct`, `protein_pct`, `fat_pct`), `menu_allocations: list[MenuAllocationItem] | None` (`group_id`, `units` — one entry per equivalency group the nutritionist has allocated exchanges to).
- **Inputs only are persisted** — no derived values (BMI, GER, macro grams, running totals) are stored anywhere; the client recomputes them from these inputs plus its own formula code, so there's never a stored number that can drift from the formula that produced it. This mirrors how `evaluation` already stores raw measurements, never a derived BMI.
- Three new section-scoped endpoints, each merging only the provided fields into whatever's already saved, matching `PATCH /consultations/{id}/evaluation`'s exact behavior: `PATCH /consultations/{id}/requirement`, `PATCH /consultations/{id}/distribution`. `PATCH /consultations/{id}/menu` is the one exception — its payload is `{allocations: [...]}` and each call **replaces** the full list (there's no meaningful field-level merge for "the current set of exchange counts"; an empty list is a legitimate save, clearing all allocations, not an empty-payload rejection).
- `ConsultationOut`/`_serialize` gain the three new sections.

## Out of Scope

- Any server-side validation that `carbs_pct + protein_pct + fat_pct == 100` — matches this service's existing "store what's given" posture (evaluation/close don't validate their inputs either); the client is responsible for that UX.
- The equivalency group catalog itself — already exists (`026-back-equivalencies-catalog`), consumed read-only by the client for the Menú step; nothing here adds or changes catalog data.
- Branded PDF, email/WhatsApp send, InBody OCR — still out of scope per `027-back-consultations-foundation`.

## Baseline Behavior

- `Consultation` had `evaluation`/`private_notes`/`next_appointment_id` as its only content sections; steps 3–5 of the nutritionist-facing wizard had nothing to save to and rendered a placeholder.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` gains the calculator UI + client-side formula code that consumes this (`031-front-consultation-requirement-menu`).

## Acceptance Criteria

1. Given a nutritionist saves part of the requirement section, then later saves a different part, then both parts are present on read — a partial save never overwrites fields it didn't touch (same guarantee as `evaluation`).
2. Given a nutritionist saves the distribution section with an empty payload (all fields null), then the request is rejected with 400 — same guardrail as `evaluation`/`close`.
3. Given a nutritionist saves a menu allocation list, then saves a different list (including an empty one), then the stored list is fully replaced by the latest call, not merged.
4. Given a consultation has never had any of these three sections saved, then reading it returns `null` for all three, not empty objects.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 110/110 green (6 new tests in `test_consultations_service.py`: merge-only-provided-fields + empty-payload-rejection for requirement and distribution, replace-full-list + empty-list-clears for menu).
- Router/module smoke and wrapper guardrail tests already cover this module by name — no per-endpoint change needed, confirmed still passing.
