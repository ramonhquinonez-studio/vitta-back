# Implementation Plan: Consultation Session Foundation

**Branch**: `027-back-consultations-foundation` | **Date**: 2026-08-19 | **Spec**: `specs/027-back-consultations-foundation/spec.md`

## Summary

A new module mirroring `equivalencies`' shape exactly (domain/application/infrastructure/presentation, hexagonal), modeling the consultation as its own top-level entity rather than fields bolted onto `Appointment` — an appointment can be rescheduled/canceled independent of whether a consultation was ever drafted for it, and "freeze as immutable version" wants a record whose identity is the clinical encounter, not the calendar slot. This was decided (with rationale) in the published proposal ahead of this build.

## Steps

1. `consultations/domain/entities.py`: `EvaluationSnapshot` (all-optional dataclass) and `Consultation` (owner-scoped, `status: "draft" | "completed"`, `current_step: int`).
2. `consultations/domain/repositories.py`: `ConsultationsRepository` protocol — `find_open_draft`, `create_draft`, `get_for_owner`, `update_for_owner` (generic top-level `$set`), `update_evaluation_for_owner` (section-scoped merge), `update_close_for_owner`, `complete_for_owner`.
3. `consultations/application/consultations_service.py`: `start` (find-or-create, backfilling `appointment_id` onto an existing draft when missing), `get_consultation`, `update_consultation`, `update_evaluation`, `update_close` (all three build an `updates` dict from only the non-`None` kwargs, raising `ValueError` on an empty payload — same convention as `AppointmentsService.update_appointment`), `complete` (raises `ValueError` if already completed).
4. `consultations/infrastructure/mongo_consultations_repository.py`: `update_evaluation_for_owner` reads the current document, merges the provided fields into the existing `evaluation` sub-document (via `dataclasses.asdict`), and writes the whole merged sub-document back in one `$set` — avoids dotted-path update complexity across seven optional fields while still only overwriting what was actually provided.
5. `app/schemas/consultation.py` + `consultations/presentation/router.py`: `POST /start`, `GET/PATCH /{id}`, `PATCH /{id}/evaluation`, `PATCH /{id}/close`, `POST /{id}/complete`. Request bodies use camelCase `validation_alias` (matching every other module's convention for the Dart client).
6. `app/routers/consultations.py` thin wrapper; registered in `main.py`; added to both router guardrail tests (`test_router_wrapper_guardrails.py`, `test_module_router_smoke.py`).
7. `app/db/init_indexes.py`: two indexes on `consultations` matching the actual query shapes in use.
8. Tests: `test_consultations_service.py` (10 tests) against a fake in-memory repository, mirroring `test_appointments_service.py`'s `dataclasses.replace`-based fake pattern.

## Constraints

- `find_open_draft` resolves by `(owner_id, patient_id, status="draft")` only — not scoped to a specific `appointment_id` — so a nutritionist resuming from a different appointment (or from a future non-appointment entry point) still reaches the same in-progress draft. A patient is assumed to never have two concurrent open drafts.
- Evaluation fields deliberately don't reuse `BodyCompositionMetrics` (the existing 19-field InBody schema) — this is a lighter, consultation-native snapshot (weight/height/%fat/three circumferences/notes) distinct from a full InBody scan, which remains its own separate concept reachable independently (as it already is from appointment detail, per `022-appointment-driven-plan-and-inbody-workflow`). Merging the two was considered and rejected: it would tie a section-autosaved draft to InBody's atomic single-POST creation semantics for no real benefit at this phase.
