# Feature Specification: Article Source URL

**Feature Branch**: `063-back-article-source-url`
**Created**: 2026-08-27
**Status**: Draft
**Type**: Feature

## Objective

User request: patients need a way to verify the information in "Biblioteca nutricional" articles. The MedlinePlus sync (`060-back-medlineplus-content-library`) already fetches each article's real source URL to build its `_id` slug, but discards it. This adds a `source_url` field, mirroring `video_url`'s exact shape everywhere, populated automatically for MedlinePlus content and optionally settable by a nutritionist for their own articles.

## In Scope

- `source_url: Optional[str]` on `Article` (domain entity), `ArticleOut`/`ArticleIn`/`ArticleUpdate` (schemas), the Mongo repository's create/read paths, and the separate patient-facing merged serializer in `me/infrastructure/mongo_me_repository.py` (`_article_dict` — a distinct code path from `content_library`'s own `_to_entity`, found the same way `photo_url` needed a second pass-through in `062-back-workout-log-session-photo`).
- `sync_medlineplus_content_library.py` now stores the real MedlinePlus page URL it already fetches (previously discarded after deriving the `_id` slug from it).

## Out of Scope

- No backfill tooling beyond re-running the existing idempotent sync script (already re-run live as part of this change — see Validation).
- No change to the 5 hand-curated seed articles (`seed_content_library.py`) — they have no real external source to cite; `source_url` reads `null` for them, same as any nutritionist-authored article that doesn't set one.

## Baseline Behavior

`Article`/`ArticleOut` had no source-attribution field. `sync_medlineplus_content_library.py` fetched `raw["url"]` from MedlinePlus's XML response only to slugify it into the document's `_id`.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_app`'s `062-front-article-source-verification` (patient-facing "Verificar información" link) and `nutri_pro`'s `070-front-article-source-url` (authoring field + coach-side link) both consume this field.

## Acceptance Criteria

1. Given a MedlinePlus-synced article, then `source_url` is its real `https://medlineplus.gov/...` page.
2. Given a nutritionist creates or updates their own article with `source_url` set, then it round-trips through `GET /content/articles/mine`.
3. Given an article has no source (hand-curated seed content, or a nutritionist who didn't set one), then `source_url` serializes as `null`.
4. Given a patient calls `GET /me/articles`, then platform articles carry the same `source_url` as the coach-facing `GET /content/articles/platform` view.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 225/225 green (additive optional field, no existing fixture broken).
- Live verification against the running local server: re-ran `sync_medlineplus_content_library.py` (110 platform articles total, 105 now carry a real `source_url` — the other 5 are the hand-curated seed articles, exactly as expected); confirmed via direct DB query and via `GET /content/articles/platform` (coach) and `GET /me/articles` (patient) that the field appears correctly; created a throwaway nutritionist-authored article with a manually set `source_url` via `POST /content/articles`, confirmed it round-trips through `GET /content/articles/mine`, then deleted it.

## Documentation

- New `nutri_back/specs/063-back-article-source-url/{spec.md,plan.md,tasks.md}`, `SPEC_ROADMAP.md` append.
