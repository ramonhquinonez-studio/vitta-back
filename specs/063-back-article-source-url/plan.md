# Implementation Plan: Article Source URL

**Feature Branch**: `063-back-article-source-url`

## Summary

Adds `source_url` end-to-end through `content_library`, mirroring the existing `video_url` field's exact shape at every layer, plus captures the value the MedlinePlus sync already fetches but was discarding.

## Steps

1. **`app/modules/content_library/domain/entities.py`**: `Article` gains `source_url: str | None = None`.
2. **`app/schemas/content_library.py`**: `ArticleOut`, `ArticleIn`, `ArticleUpdate` all gain `source_url: Optional[str] = None`.
3. **`app/modules/content_library/infrastructure/mongo_content_library_repository.py`**: `create_for_owner` includes `"source_url": payload.get("source_url")`; `_to_entity` includes `source_url=document.get("source_url")`. `update_for_owner` needed no change — it already `$set`s the raw payload dict.
4. **`app/modules/me/infrastructure/mongo_me_repository.py`** `_article_dict` (the separate patient-facing merged-feed serializer for `GET /me/articles`): adds `"source_url": document.get("source_url")`.
5. **`app/scripts/sync_medlineplus_content_library.py`**: the `doc` dict built in `sync()` gains `"source_url": raw["url"]` (the value was already being fetched, just previously used only for the `_id` slug).
6. **Live backfill**: re-run `python -m app.scripts.sync_medlineplus_content_library` — idempotent upsert by stable `_id`, safe to re-run, backfills `source_url` on all 105 already-synced MedlinePlus documents without duplicating anything.

## Constraints

- No test fixture changes needed — `Article(...)` and the JSON schemas are all keyword-based with the new field defaulting to `None`.
