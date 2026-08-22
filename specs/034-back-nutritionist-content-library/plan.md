# Implementation Plan: Nutritionist-Authored Content Library

**Branch**: `034-back-nutritionist-content-library` | **Date**: 2026-08-21 | **Spec**: `specs/034-back-nutritionist-content-library/spec.md`

## Summary

Extends the existing `content_library` module (`032`) with owner-scoped CRUD, reusing `recipes`' exact owner-scoping pattern (`_as_oid`, `{"_id": doc_oid, "owner_id": owner_oid}` filter for update/delete). Adds one new `me` endpoint (`GET /me/articles`) mirroring `list_recipe_collections`'s structure, with one deliberate difference: it does not early-return `[]` for a patient with no assigned nutritionist, since platform content should still be visible.

## Steps

1. `content_library/domain/entities.py`: `Article` gains `owner_id: str | None = None`, `video_url: str | None = None`.
2. `content_library/domain/repositories.py`: `ContentLibraryRepository` protocol gains `list_for_owner`, `create_for_owner`, `update_for_owner`, `delete_for_owner` — same shape as `recipes/domain/repositories.py`.
3. `content_library/infrastructure/mongo_content_library_repository.py`: implements the above against `content_articles`, owner-scoped by `ObjectId` (`_as_oid` helper copied from `mongo_recipes_repository.py`). Existing `list_articles()` (platform-only) untouched.
4. `content_library/application/content_library_service.py`: `list_my_articles`, `create` (validates title + body-or-video), `update`, `delete` — mirrors `RecipesService`.
5. `app/schemas/content_library.py`: `ArticleOut` gains `owner_id`/`video_url`; new `ArticleIn`/`ArticleUpdate`/`ArticleSectionIn`.
6. `content_library/presentation/router.py`: `GET /content/articles/mine`, `POST /content/articles`, `PATCH /content/articles/{id}`, `DELETE /content/articles/{id}` — same try/except LookupError→404 / ValueError→400 shape as `recipes/presentation/router.py`. No changes to `app/routers/content_library.py` (thin wrapper already re-exports the module router, so new routes are live automatically) or `main.py`.
7. `me` module (`domain/repositories.py`, `infrastructure/mongo_me_repository.py`, `application/me_service.py`, `presentation/router.py`): `list_articles(owner_id)` — repository queries `content_articles` for `owner_id: None` (platform; MongoDB's `{field: null}` matches both explicit null and a missing field, so this correctly picks up documents with no `owner_id` key at all) unioned with the caller's owner_id when present, returned as raw dicts (matching the sibling `/me/recipe_collections`/`/me/education_videos` endpoints' `response_model=list[dict]` convention — `me` queries collections directly rather than importing another module's service).
8. Tests: `tests/test_content_library_service.py` — new `_FakeOwnerScopedRepository` + 5 tests (create requires title, create requires body-or-video, video-only allowed, create→update→delete round trip, update rejects a non-owned article). `tests/test_me_service.py` — `_FakeMeRepository.list_articles` + 2 tests (merges platform + owner content; falls back to platform-only with no linked patient).

## Constraints

- `ArticleUpdate.sections` is `Optional[list[ArticleSectionIn]] = None` so a partial update (e.g. title-only) doesn't wipe existing sections — but the `nutri_pro` client always sends the full current `sections` on every save (mirroring how `RecipeModel.encodeDraft` always sends the full `ingredients` list), so in practice this is always a full replace from that client, same as recipes.
- No migration for existing platform articles — they already lack an `owner_id` field, which is exactly what the `None`-owner query relies on; no backfill needed.
