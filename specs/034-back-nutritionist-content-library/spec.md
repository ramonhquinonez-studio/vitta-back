# Feature Specification: Nutritionist-Authored Content Library

**Feature Branch**: `034-back-nutritionist-content-library`
**Created**: 2026-08-21
**Status**: Draft
**Type**: Feature

## Objective

`032-back-content-library` explicitly scoped out "nutritionist-authored content" as out-of-scope, noting the platform-curated library is Vitta editorial content, not per-nutritionist data. The nutritionist asked directly for a way to add their own articles/videos/text for their own patients, as a section clearly independent from Recetario (the `recipes` module, which the nutritionist had confused it with in `nutri_pro`'s UI). This extends `content_library` to support owner-scoped articles alongside the existing platform ones, reusing the exact `owner_id`-scoped-collection pattern already proven for `recipes`/`recommendations`, rather than resurrecting the dormant, never-wired `/me/education_videos` precedent (video-only, no CRUD, orphaned on both frontends).

## In Scope

- `Article` gains `owner_id: str | None` (`None` = platform/global, unchanged) and `video_url: str | None`.
- Nutritionist CRUD under the existing `/content` prefix: `GET /content/articles/mine`, `POST /content/articles`, `PATCH /content/articles/{id}`, `DELETE /content/articles/{id}` — all owner-scoped, mirroring `recipes/presentation/router.py`'s shape exactly.
- `GET /me/articles` — patient-facing merged read: platform articles plus the patient's own assigned nutritionist's articles, mirroring `GET /me/recipe_collections`'s owner-resolution pattern (`me_service` resolves `patient.owner_id`, delegates to `me`'s own repository query — no cross-module service import, consistent with `list_recipe_collections`/`list_education_videos`). Unlike those two, this endpoint still returns platform content even for a patient with no assigned nutritionist.
- Validation: `title` required; at least one of body text (non-empty `sections[].text`) or `video_url` required — an article must have something to actually show.

## Out of Scope

- Any change to the existing unscoped `GET /content/articles` (platform-only) — untouched, still used as-is.
- Migrating/deleting the dormant `education_videos` collection or its `/me/education_videos` endpoint — left as-is; this feature does not use it.
- Rich structured sections in the nutritionist-authoring UI (multiple titled sections with bullets) — the nutritionist form (`nutri_pro`) writes a single body-text section; the underlying `sections: list[dict]` storage still supports the richer platform-article shape, so this is a UI simplification, not a data-model restriction.

## Baseline Behavior

Nutritionists had no way to add their own educational content anywhere in the system. The only content patients could see in "Biblioteca nutricional" was the 5 platform-curated articles from `032`. `nutri_pro` had no CRUD screen for anything called "Biblioteca nutricional" at all — its only book-icon entry point actually opened Recetario (recipe authoring), an unrelated feature that happened to share the same display name.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` gains spec `033-front-nutritionist-content-library` (new CRUD module + Perfil-tab entry point + Recetario tooltip fix); `nutri_app`'s `content_library` module switches its read endpoint from `/content/articles` to `/me/articles` and renders `video_url`/an "authored by nutritionist" indicator.

## Acceptance Criteria

1. Given a nutritionist creates an article with only body text (no video), when they call `POST /content/articles`, then it succeeds and is scoped to their own `owner_id`.
2. Given a nutritionist creates an article with only a `video_url` (no body text), then it also succeeds — video-only content is valid.
3. Given a nutritionist submits neither body text nor a `video_url`, then the request is rejected with 400.
4. Given a patient with an assigned nutritionist who has authored 2 articles, when the patient calls `GET /me/articles`, then the response contains the 5 platform articles plus their nutritionist's 2, and no other nutritionist's content.
5. Given a patient with no assigned nutritionist, when they call `GET /me/articles`, then they still see the 5 platform articles (not an empty list).
6. Given a nutritionist tries to `PATCH`/`DELETE` another nutritionist's article by id, then the request 404s (owner-scoped lookup fails, same as `recipes`' collection-not-owned behavior).

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 121/121 green (7 new tests: 5 in `test_content_library_service.py`, 2 in `test_me_service.py`).
- Live manual verification against the running backend: registered a throwaway nutritionist + a patient linked via invite code, created one text-only and one video-only article, confirmed `GET /content/articles/mine` lists both, `PATCH` and `DELETE` round-trip correctly, `POST` with neither body nor video 400s, and the linked patient's `GET /me/articles` returns exactly the 5 platform articles plus the 2 owner articles (verified by owner_id in the response). Test articles and DB rows deleted after verification; throwaway accounts left in place (harmless, consistent with this session's existing throwaway-test-account pattern).
