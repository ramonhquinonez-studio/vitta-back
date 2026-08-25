# Tasks: Custom Check-In Forms

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `checkin/domain` + `infrastructure` + `application`.
- [x] T003 `schemas/checkin.py` + `checkin/presentation/router.py`.
- [x] T004 `routers/checkin.py` wrapper + wiring en `main.py`.
- [x] T005 `me` module: `list_checkin_templates`/`submit_checkin_response`/`list_checkin_responses` + endpoints.
- [x] T006 `patients` module: `list_checkin_responses` + endpoint `GET /{patient_id}/checkin-responses`.
- [x] T007 Tests: `test_checkin_service.py` (8 casos), `test_me_service.py` (+6), `test_patients_service.py` (+2).

## Phase 3: Validation

- [x] T008 Suite completa → 179/179 verde.
- [x] T009 Verificación en vivo end-to-end (los 5 tipos de campo, validación de campos requeridos, lectura cruzada paciente/nutriólogo, aislamiento entre tenants, archivado sin borrado).

## Evidence

- Suite completa: 179/179 verde.
- Verificación en vivo: plantilla creada con un campo de cada tipo; envío incompleto rechazado con 400 (`Missing required field: Estado de ánimo`); envío completo visible en ambos endpoints de lectura; nutriólogo no relacionado recibe 404; plantilla archivada desaparece de la lista activa del paciente pero sigue resolviéndose por id. Cuentas y datos de prueba limpiados al final.
