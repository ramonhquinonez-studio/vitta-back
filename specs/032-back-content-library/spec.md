# Feature Specification: Nutrition Education Content Library

**Feature Branch**: `032-back-content-library`
**Created**: 2026-08-20
**Status**: Draft
**Type**: Feature

## Objective

Give the backend a real home for `nutri_app`'s "Biblioteca nutricional" content, which today is a hardcoded `const` article list inside `nutrition_library_page.dart` with no backend behind it. This is platform-curated, read-only editorial content (macros, hydration, metabolism, label-reading) — not per-nutritionist or per-patient data — so it's modeled the same way as the SMAE equivalencies catalog (`026-back-equivalencies-catalog`): a global, seeded, read-only collection.

## In Scope

- New `content_library` module: `content_articles` collection (seeded, global, 5 articles at launch — the exact content already authored in the Flutter client), each with `category`/`title`/`description`/`read_time`/`emoji`/`order`/`sections` (each section: `title`/`text`/optional `bullets`).
- `GET /content/articles` — the full article catalog, sorted by `order`.
- `app/scripts/seed_content_library.py` — idempotent seed script migrating the 5 existing articles verbatim.

## Out of Scope

- Nutritionist-authored content — this is Vitta-curated editorial content, not per-nutritionist data. No CRUD endpoints, no authoring UI in `nutri_pro`.
- The unrelated, pre-existing `/me/education_videos` endpoint (per-nutritionist video feed with no authoring UI anywhere) — untouched, stays orphaned on the frontend.
- Search/filtering server-side — the client already filters client-side by category/text query over the small (5-article) catalog; no need for a search endpoint at this scale.

## Baseline Behavior

- No content-library concept existed anywhere in the backend. The Flutter client's `nutrition_library_page.dart` rendered a hardcoded `const` list of 5 articles with no data layer at all.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`

## Acceptance Criteria

1. Given any authenticated user, when they call `GET /content/articles`, then all 5 articles are returned, sorted by `order`, with their full section content (including bullets where present).
2. Given the seed script is re-run, then articles are upserted by their stable `_id`, not duplicated.
3. Given a section has no `bullets` field, then `bullets` is `null`/absent in the response rather than an empty list or error.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 104/104 green (1 new test in `test_content_library_service.py`, both router guardrail/smoke tests extended for the new module).
- `python app/scripts/seed_content_library.py` → 5 articles seeded (idempotent — re-running upserts, no duplicates).
