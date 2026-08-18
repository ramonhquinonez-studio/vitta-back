# Tasks: Plan Assignment History

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `patients/domain/repositories.py`: método `list_plan_assignments`.
- [x] T003 `mongo_patients_repository.py`: implementación con snapshot de `plan_name`.
- [x] T004 `patients_service.py`: método de servicio.
- [x] T005 `router.py`: `GET /{patient_id}/plan_assignments`.
- [x] T006 `tests/test_patients_service.py`: fake actualizado; 2 tests nuevos.

## Phase 3: Validation

- [x] T007 Suite completa → 64/64 verde.
- [x] T008 `curl GET /patients/{id}/plan_assignments` → historial real correcto.
- [x] T009 Datos de prueba obsoletos (asignaciones a planes ya eliminados de pruebas anteriores) limpiados directamente en la base de datos.

## Evidence

- Suite completa: 64/64, verde.
- `curl` → historial de Ramon Quinonez muestra únicamente la asignación real ("Plan Semanal Demo", 2026-08-15), tras limpiar 3 asignaciones obsoletas que apuntaban a planes de prueba ya eliminados.
