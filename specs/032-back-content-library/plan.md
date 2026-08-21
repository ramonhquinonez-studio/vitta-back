# Implementation Plan: Nutrition Education Content Library

**Branch**: `032-back-content-library` | **Date**: 2026-08-20 | **Spec**: `specs/032-back-content-library/spec.md`

## Summary

A new module mirroring the `equivalencies` module's shape exactly (domain/application/infrastructure/presentation, `Protocol`-based repository, typed Pydantic response models) — read-only, single endpoint, global (not owner-scoped) data.

## Steps

1. `content_library/domain/entities.py`: `Article` (string `id` — a stable slug like `macronutrientes`, not an `ObjectId`, since it's a small fixed catalog referenced by key; `order: int` for deterministic sort) and `ArticleSection` (`title`, `text`, `bullets: list[str] | None`).
2. `content_library/domain/repositories.py`: `ContentLibraryRepository` protocol, one method (`list_articles`).
3. `content_library/infrastructure/mongo_content_library_repository.py`: reads `content_articles` sorted by `order` ascending.
4. `content_library/application/content_library_service.py`: thin pass-through (no validation needed — read-only, no user input).
5. `app/schemas/content_library.py` + `content_library/presentation/router.py`: `GET /content/articles`, `response_model=list[ArticleOut]`, `Depends(get_current_user)` (auth required, matches `GET /equivalencies/groups`'s precedent of gating global data behind auth rather than leaving it public).
6. `app/routers/content_library.py` thin wrapper; registered in `main.py`; added to both router guardrail tests (`test_router_wrapper_guardrails.py`, `test_module_router_smoke.py`).
7. `app/scripts/seed_content_library.py`: 5 `ARTICLES` transcribed verbatim from `nutri_app`'s `nutrition_library_page.dart` — idempotent via `update_one(..., upsert=True)` by stable `_id`.
8. Tests: `test_content_library_service.py` (fake-repo unit test).

## Constraints

- Content stays platform-curated and read-only for this MVP slice — no nutritionist authoring, no patient interaction (likes/bookmarks) beyond reading. If a future phase needs authoring, it's a distinct, larger feature (needs `nutri_pro` UI), not an extension of this endpoint.
- Article `_id`s are stable slugs chosen to match the article subject (e.g. `macronutrientes`, `hidratacion`) so future edits to the seed script upsert in place rather than creating duplicates.
