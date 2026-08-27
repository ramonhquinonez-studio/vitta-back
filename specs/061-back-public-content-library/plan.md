# Implementation Plan: Filtered Platform Articles Endpoint (Backend)

**Branch**: `061-back-public-content-library` | **Date**: 2026-08-26 | **Spec**: `specs/061-back-public-content-library/spec.md`

## Summary

Additive endpoint mirroring `exercise_library`'s already-established platform-tier pattern exactly — same filter, same layering, no schema changes.

## Steps

1. `app/modules/content_library/domain/repositories.py`: `list_platform_articles()` added to the `ContentLibraryRepository` `Protocol`.
2. `app/modules/content_library/infrastructure/mongo_content_library_repository.py`: `list_platform_articles()` — `find({"owner_id": None}).sort("order", 1)`, reusing the existing `_to_entity`.
3. `app/modules/content_library/application/content_library_service.py`: `list_platform_articles()` passthrough.
4. `app/modules/content_library/presentation/router.py`: `GET /content/articles/platform`, `require_role("nutritionist")` (matches `exercise_library`'s platform-endpoint gating).
5. `tests/test_content_library_service.py`: `_FakeOwnerScopedRepository` gains a `platform` list + `list_platform_articles()`; new test confirms it returns only platform content, not a nutritionist's own.

## Constraints

- Deliberately does not touch or reconsider the existing unfiltered `GET /content/articles` route — out of scope here.
