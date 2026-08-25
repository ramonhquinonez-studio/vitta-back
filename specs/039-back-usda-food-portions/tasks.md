# Tasks: USDA Food Portion Weights

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `schemas/plan.py`: `unit_gram_weight` en `PlanMealItem`.
- [x] T003 `domain/entities.py`: `FoodPortion`.
- [x] T004 `domain/repositories.py`: `get_portions` en el Protocol.
- [x] T005 `infrastructure/usda_fdc_repository.py`: `_get_with_retry` compartido + `get_portions`.
- [x] T006 `application/nutrition_lookup_service.py`: `get_portions`.
- [x] T007 `schemas/nutrition_lookup.py` + `presentation/router.py`: `GET /nutrition/food/{fdc_id}/portions`.
- [x] T008 Test nuevo en `tests/test_nutrition_lookup_service.py`.

## Phase 3: Validation

- [x] T009 Suite completa → 127/127 verde.
- [x] T010 Verificación en vivo contra el backend real.

## Evidence

- Suite completa: 127/127 verde.
- Verificación en vivo: `GET /nutrition/food/169967/portions` devolvió 5 porciones reales de USDA para brócoli cocido.
