# Tasks: Food Equivalency (SMAE) Catalog

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `equivalencies/domain/`: entidades + repositorio protocol.
- [x] T003 `mongo_equivalencies_repository.py`: implementación (merge global + owned).
- [x] T004 `equivalencies_service.py`: validaciones.
- [x] T005 `app/schemas/equivalencies.py` + `presentation/router.py`.
- [x] T006 `app/routers/equivalencies.py` + registro en `main.py`.
- [x] T007 `app/schemas/plan.py`: campos de equivalencia en `PlanMealItem`.
- [x] T008 `app/scripts/seed_equivalencies.py`: 16 grupos + 57 alimentos.
- [x] T009 Tests nuevos + guardrails de router actualizados.

## Phase 3: Validation

- [x] T010 Suite completa → 76/76 verde.
- [x] T011 Seed ejecutado → 16 grupos, 57 alimentos.
- [x] T012 `curl GET /equivalencies/groups` → 16 grupos con macros.
- [x] T013 `curl GET /equivalencies/foods?group_id=` → alimentos reales del grupo.
- [x] T014 `curl POST/DELETE /equivalencies/foods` → alimento personalizado creado, verificado, eliminado.
- [x] T015 `curl POST /plans` con campos de equivalencia en un item → round-trip exacto confirmado, plan de prueba eliminado.

## Evidence

- Suite completa: 76/76, verde.
- Seed: "Grupos: 16 actualizados/creados." / "Alimentos: 57 nuevos de 57 en el catálogo base."
- `curl`: grupo "cereales_sin_grasa" con 6 alimentos reales (Tortilla de maíz, Arroz cocido, etc.); alimento personalizado "Guayaba" creado y eliminado correctamente.
