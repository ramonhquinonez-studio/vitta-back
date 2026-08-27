# Feature Specification: Filtered Platform Articles Endpoint (Backend)

**Feature Branch**: `061-back-public-content-library`
**Created**: 2026-08-26
**Status**: Draft
**Type**: Feature

## Objective

`nutri_pro`'s own "Biblioteca nutricional" screen (`GET /content/articles/mine`) only ever showed a nutritionist's own authored articles — by design, but it meant a coach had no way to browse the platform-curated content (`056-back-medlineplus-content-library`'s 110 MedlinePlus-sourced articles) their own patients already see. The existing `GET /content/articles` route can't be reused for this: it's completely unfiltered (`find({})`), returning every nutritionist's private articles too — a real privacy leak if exposed as a "browse public content" feature.

## In Scope

- `GET /content/articles/platform` — nutritionist-only, returns only `owner_id: None` articles, mirroring `exercise_library`'s exact `GET /exercise-library/platform` pattern (same filter shape, same additive change — no schema/entity changes needed).

## Out of Scope

- The existing unfiltered `GET /content/articles` route is left as-is (not reused, not removed) — out of scope to reconsider its access model here.
- No new "save a copy" endpoint — copying a platform article into a nutritionist's own library reuses the existing `POST /content/articles` create endpoint unchanged, fed with the platform article's own field values from the frontend.

## Baseline Behavior

No endpoint existed that returned platform-only articles to a nutritionist; the only two options were "everyone's articles" (`GET /content/articles`, a privacy risk to expose) or "just mine" (`GET /content/articles/mine`).

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: `nutri_pro` spec `066-front-public-content-library` consumes this.

## Acceptance Criteria

1. Given platform articles exist, when a nutritionist calls `GET /content/articles/platform`, then only `owner_id: None` articles are returned, sorted by `order`.
2. Given other nutritionists have their own private articles, then those never appear in this endpoint's response.
3. Given a nutritionist has no own articles yet, then `GET /content/articles/mine` still correctly returns `[]` (unaffected by this change).

## Validation

- Full backend unittest suite green (225/225 — 1 new test added).
- Live-curl verification against the running local server with a fresh QA nutritionist account: confirmed `GET /content/articles/platform` returns all 110 real synced articles; confirmed `GET /content/articles/mine` returns `[]` for the same fresh account; confirmed copying a platform article's fields via the existing `POST /content/articles` produces an independent owned copy, then appears in `GET /content/articles/mine`. QA account and its one test article cleaned up afterward.
