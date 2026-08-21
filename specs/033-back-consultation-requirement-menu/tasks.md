# Tasks: Consultation Requirement/Distribution/Menu

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `consultations/domain/entities.py`: `RequirementInput`, `DistributionInput`, `MenuAllocationItem` + campos nuevos en `Consultation`.
- [x] T003 `consultations/domain/repositories.py`: métodos nuevos del protocol.
- [x] T004 `mongo_consultations_repository.py`: merge de requirement/distribution, replace de menu, deserialización en `_to_entity`, campos iniciales en `create_draft`.
- [x] T005 `consultations_service.py`: `update_requirement`/`update_distribution`/`update_menu`.
- [x] T006 `app/schemas/consultation.py` + `presentation/router.py`: tres endpoints PATCH nuevos + `_serialize` extendido.
- [x] T007 Tests nuevos en `test_consultations_service.py` (6 casos).

## Phase 3: Validation

- [x] T008 Suite completa → 110/110 verde.
- [x] T009 Confirmado que los guardrails de router (`test_router_wrapper_guardrails.py`, `test_module_router_smoke.py`) no requieren cambios — ya cubren el módulo por nombre.

## Evidence

- Suite completa: 110/110, verde (104 previos + 6 nuevos).
