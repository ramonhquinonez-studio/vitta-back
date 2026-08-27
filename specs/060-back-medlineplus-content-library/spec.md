# Feature Specification: MedlinePlus-Synced Platform Articles (Backend)

**Feature Branch**: `060-back-medlineplus-content-library`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

`content_library`'s platform tier (`Article.owner_id: Optional[str]`, `null` = platform-curated) already existed with exactly 5 hand-written seed articles (`seed_content_library.py`). This adds real, ongoing content volume by syncing from **MedlinePlus** (NIH / National Library of Medicine) — a free, keyless, government-produced health-information service with native Spanish content, confirmed live before building against it (no signup, no API key, `db=healthTopicsSpanish` query, public-domain-adjacent government content with a simple attribution requirement).

## In Scope

- `app/scripts/sync_medlineplus_content_library.py` — idempotent upsert-by-stable-id sync script (not a public endpoint, run manually), mirroring `seed_content_library.py`'s pattern exactly (`owner_id: None`, same `content_articles` collection, same document shape — **zero changes to the existing `content_library` module's schema, router, service, or repository**, since the platform tier already fully supports this).
- Pulls four confirmed-live, sampled-for-relevance MedlinePlus groups: "Alimentos y nutrición," "Bienestar y estilo de vida," "Diabetes mellitus" (diet/glucose-management content, a natural fit for a nutrition-coaching app), and "Aptitud física y ejercicio" (complements this app's own workout module) — deduplicated by URL slug (some topics belong to more than one group). Broader clinical groups ("Sangre, corazón y circulación," "Sistema digestivo," "Embarazo") were tried and rejected after sampling their actual titles — mostly general disease/clinical content (strokes, birth control, GI disorders), not nutrition-relevant, that would have diluted the library.
- HTML-to-`sections` conversion: MedlinePlus returns one flowing HTML summary per topic, not pre-split sections like the hand-authored seed content — a small stdlib `html.parser.HTMLParser` subclass extracts paragraph text and bullet-list items into a single `ArticleSection` per article (no per-paragraph splitting, to avoid a wall of blank section titles).
- Attribution: every synced article's body ends with "Fuente: MedlinePlus.gov," per their stated terms (no logo use, no implied endorsement).

## Out of Scope

- No new API endpoint, schema field, or frontend change — `GET /me/articles`'s existing platform+nutritionist merge, and both apps' existing rendering/badge logic, pick this content up automatically.
- No automatic/scheduled re-sync — run manually when the library needs refreshing (matches every other seed/sync script in this codebase).
- No additional MedlinePlus groups beyond the two synced — trivially extensible (`_GROUPS` dict) if more content is wanted later.

## Baseline Behavior

The platform article tier existed but held only 5 hand-written articles.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: none — both `nutri_pro` and `nutri_app` already fully support the platform-article mechanism this reuses; no code changes needed on either side.

## Acceptance Criteria

1. Given the sync script runs, then it upserts one `content_articles` document per unique MedlinePlus topic across both groups, with `owner_id: None`.
2. Given a patient (assigned or unassigned) calls `GET /me/articles`, then the synced MedlinePlus articles appear alongside the existing hand-curated ones, correctly categorized by their MedlinePlus group name.
3. Given the script is re-run, then no duplicate documents are created (idempotent upsert by stable slug-derived `_id`).
4. Given a synced article, then its body text ends with the required MedlinePlus attribution line.

## Validation

- Full backend unittest suite green (224/224, unaffected — pure data script, no existing code touched, matching `seed_content_library.py`'s own no-test-coverage precedent).
- Live run against the real MedlinePlus API and local Mongo, twice (once with the initial 2 groups, again after expanding to 4): 117 articles processed across all 4 groups, 110 distinct documents synced (some topics cross-listed between groups, correctly upserted rather than duplicated). Verified via `GET /me/articles` against a real (unassigned) QA patient account after the first sync (92 articles: 5 hand-curated + 87 MedlinePlus), and via a direct Mongo category-count check after the expansion (110 total: 54 nutrition, 23 wellness, 19 diabetes, 9 exercise, 5 hand-curated). QA patient account cleaned up afterward; all real synced articles were kept (legitimate content, not throwaway test data).
