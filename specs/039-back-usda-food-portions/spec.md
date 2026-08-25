# Feature Specification: USDA Food Portion Weights

**Feature Branch**: `039-back-usda-food-portions`
**Created**: 2026-08-24
**Status**: Draft
**Type**: Feature

## Objective

`038-back-usda-nutrition-lookup`'s search only unlocked USDA-sourced macro autofill for items whose unit was already grams — every other unit (`taza`, `pieza`, `cucharada`...) still needed hand-entry, since a generic "1 taza = X g" constant is wrong for most foods (a cup of rolled oats, cooked rice, and milk are three very different weights, as the earlier manual backfill of this session's demo plan discovered the hard way). The user asked for unit-to-gram equivalents to be real and food-specific rather than a guessed constant. USDA FDC publishes real, measured household-portion weights per food (`foodPortions`) — this exposes that data.

## In Scope

- Extend the existing `nutrition_lookup` module: `FoodPortion` entity (`description`, `gram_weight`), `NutritionLookupRepository.get_portions(fdc_id)`.
- `UsdaFdcRepository.get_portions`: calls USDA's `/food/{fdcId}` detail endpoint, parses `foodPortions[].gramWeight` paired with a human-readable description built from `amount` + `modifier` (falling back to `measureUnit.name` when `modifier` is the literal `"undetermined"` USDA sometimes returns).
- `GET /nutrition/food/{fdc_id}/portions` (auth required) returns the parsed list.

## Out of Scope

- No fuzzy-matching of a nutritionist's chosen unit (e.g. "taza") against USDA's English portion descriptions (e.g. "0.5 cup, chopped") — the nutritionist picks the matching portion themselves after seeing the real list, since guessing the match risks silently pairing the wrong portion. See `038-front-controllable-units-and-portions` in `nutri_pro`.
- No caching of portion data.

## Baseline Behavior

USDA-sourced macro autofill only worked for gram-unit items; everything else had no path to a real, food-specific gram equivalent.

## Documentation Impact

- **Global docs to update**: `specs/SPEC_ROADMAP.md`.
- **Cross-repo impact**: consumed by `nutri_pro` spec `038-front-controllable-units-and-portions`, which in turn produces a `unit_gram_weight` value on `PlanMealItem` (new field, this repo's schema) that `nutri_app` spec `047-front-unit-gram-weight-display` shows to patients.
- `app/schemas/plan.py`: `PlanMealItem` gains `unit_gram_weight: Optional[float] = None` — purely additive, same low-risk pattern as every other optional field added to this model this session.

## Acceptance Criteria

1. Given `GET /nutrition/food/169967/portions` (cooked broccoli) with a valid auth token, then it returns real portions including one around 78g for "0.5 cup, chopped".
2. Given a food with no portion data, then it returns an empty list, not an error.
3. Given a `POST /plans` payload with an item carrying `unit_gram_weight: 78`, when created, then `GET /plans/{id}` returns that value unchanged; an item that omits it comes back `null`.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 127/127 green.
- Live verification against the running backend: authenticated `GET /nutrition/food/169967/portions` returned 5 real USDA portions (stalk large/280g, spear/37g, 0.5 cup chopped/78g, stalk medium/180g, stalk small/140g).
