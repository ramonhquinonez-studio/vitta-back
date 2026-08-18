# Tasks: Plan Meal Eating-Out Options

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/plan.py`: `EatingOutOption` + campo `eating_out_options` en `PlanMeal`.
- [x] T003 `tests/test_plans_service.py`: `PlanSchemaTest` nuevo.

## Phase 3: Validation

- [x] T004 Suite completa → 62/62 verde.
- [x] T005 `curl POST /plans` con `eating_out_options` → reflejado correctamente en la respuesta.
- [x] T006 `curl POST /plans/{id}/assign` + `curl GET /me/plan/active` (paciente) → mismas opciones visibles end-to-end.

## Evidence

- Suite completa: 62/62, verde.
- `curl`: plan `6a8416ced246d2c68655f0b2` con 2 `eating_out_options` en "Desayuno"; tras asignar a la paciente demo, `GET /me/plan/active` devolvió las mismas 2 opciones en el mismo meal.
