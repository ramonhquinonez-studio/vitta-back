# Implementation Plan: MedlinePlus-Synced Platform Articles (Backend)

**Branch**: `060-back-medlineplus-content-library` | **Date**: 2026-08-26 | **Spec**: `specs/060-back-medlineplus-content-library/spec.md`

## Summary

A single new standalone script, no existing code touched — `content_library`'s platform tier already supports everything this needs.

## Steps

1. New `app/scripts/sync_medlineplus_content_library.py`:
   - `_GROUPS: dict[str, str]` — MedlinePlus groupName → display emoji. Each group confirmed live via direct curl (count > 0) *and* sampled for actual title relevance before inclusion: `"Alimentos y nutrición"` (57), `"Bienestar y estilo de vida"` (32), `"Diabetes mellitus"` (19 — diet/glucose-management content), `"Aptitud física y ejercicio"` (9 — complements the app's workout module). Broader groups (`"Sangre, corazón y circulación"`, `"Sistema digestivo"`, `"Embarazo"`) were sampled and rejected — their actual titles are general clinical content (strokes, birth control, GI disorders), not nutrition-relevant.
   - `_fetch_group(group_name, retmax=100)` — `GET https://wsearch.nlm.nih.gov/ws/query?db=healthTopicsSpanish&term=group:"<name>"`, parses the XML response (stdlib `xml.etree.ElementTree`) into `{url, title, summary_html}` dicts.
   - `_SummaryParser(HTMLParser)` — stdlib HTML parsing (no new dependency), extracts all `<p>` paragraph text and `<li>` bullet text from the `FullSummary` blob.
   - `_parse_section(summary_html)` — joins all paragraphs into one `ArticleSection`-shaped dict (`title: ""`, `text`, `bullets`), appends the required "Fuente: MedlinePlus.gov" attribution line.
   - `_slug_from_url(url)` — stable id from the URL's last path segment (e.g. `drinkingwater` from `.../spanish/drinkingwater.html`), prefixed `medlineplus-` for the Mongo `_id`.
   - `_estimate_read_time(text)` — word count ÷ 200wpm, since MedlinePlus doesn't provide one.
   - `sync()` — for each group, fetch and upsert into `content_articles` with `owner_id: None`, `order` starting at 100 (after the hand-curated seed's 1–5) and incrementing per article.
   - `main()` — `connect_to_mongo`/`close_mongo_connection` bracket, matching `seed_content_library.py`'s exact shape.
2. No changes anywhere else — `app/modules/content_library/*`, `app/modules/me/infrastructure/mongo_me_repository.py`'s `list_articles`/`_article_dict`, and both frontends' rendering all already handle this document shape.

## Constraints

- Design choice: one combined section per article (not one section per paragraph) — avoids a wall of blank section-title lines in the UI, since MedlinePlus content is a flowing article, not naturally pre-sectioned like the hand-authored seed content.
- Attribution line is appended unconditionally, per MedlinePlus's stated terms.
