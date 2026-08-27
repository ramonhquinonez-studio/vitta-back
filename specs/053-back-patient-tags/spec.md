# Feature Specification: Patient Tags (Client Groups)

**Feature Branch**: `053-back-patient-tags`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

From the "Coach App Screen Audit" punch list: TrainerStudio lets a coach tag/group clients (e.g. "VIP", "Pérdida de peso") and filter the roster by tag. `Patient` has no such field.

## In Scope

- `tags: list[str]` on `Patient`, free-text, coach-defined — settable via create and update, round-tripped through `GET`.

## Out of Scope

- No separate tag entity/collection, no tag CRUD, no distinct-tags endpoint. Matches `allergies`' existing shape exactly (`list[str]`, no metadata).
- No server-side tag filtering on `GET /patients` — the roster is small enough (comfortably practice-scale, already capped at 100 per fetch) that `nutri_pro` filters client-side over the already-loaded list.

## Baseline Behavior

`Patient` had no way to group/label clients beyond free-text `notes`.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` spec `053-front-patient-tags` consumes this.

## Acceptance Criteria

1. Given a nutritionist creates a patient with `tags: ["VIP", "Grupo A"]`, then `GET /patients/{id}` returns both tags.
2. Given a nutritionist updates a patient's `tags`, then the new list fully replaces the old one (same replace semantics as `allergies`).

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → full suite green.
- Live-curl verification: create a patient with tags, update tags, confirm both round-trip through `GET`. Test data cleaned up afterward.
