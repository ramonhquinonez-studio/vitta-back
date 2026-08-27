# Tasks: Practice-Wide Analytics Dashboard

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `Patient.created_at` + `create_for_owner` lo asigna.
- [x] T003 `mongo_patients_repository.py::get_dashboard` (conteos + unión de actividad reciente).
- [x] T004 `patients_service.py::get_dashboard` (passthrough).
- [x] T005 `GET /patients/dashboard` (antes de `/{patient_id}`) + cálculo de ingreso estimado.
- [x] T006 Índices: `patients(owner_id, created_at)`, `checkin_responses(patient_id, submitted_at)`.
- [x] T007 Test: `test_patients_service.py` (+1 caso).

## Phase 3: Validation

- [x] T008 Suite completa → 207/207 verde.
- [x] T009 Verificación en vivo (conteos exactos, paciente inactivo marcado, ingreso estimado, aislamiento entre tenants).

## Evidence

- Suite completa: 207/207 verde.
- Verificación en vivo: 2 pacientes sembrados (uno con cita completada + próxima, otro sin ninguna), `session_price` configurado; el dashboard reportó `total_patients=2, new_patients_this_month=2, upcoming_appointments_this_week=1, completed_appointments_this_month=1, active_patients=1, inactive_patients=[Paciente Inactivo], estimated_revenue_this_month=500.0`. El dashboard de un segundo nutriólogo mostró todo en cero. Cuentas y datos de prueba limpiados al final.
