# Tasks: Dashboard Appointment & Revenue Trend

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `mongo_patients_repository.py`: `completed_appointments_by_month` (mismo patrón que `new_patients_by_month`).
- [x] T003 `patients/presentation/router.py`: `estimated_revenue_by_month` derivado.

## Phase 3: Validation

- [x] T004 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 225/225 verde.
- [x] T005 Verificación en vivo (`GET /patients/dashboard`).

## Evidence

- Suite completa: 225/225 verde.
- `GET /patients/dashboard` en vivo: `completed_appointments_by_month` y `estimated_revenue_by_month` presentes, 6 buckets cronológicos cada uno, contra la cuenta demo sembrada.
