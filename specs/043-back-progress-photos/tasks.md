# Tasks: Progress Photos and Nutritionist Visibility into Self-Logged Measurements

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `me/presentation/router.py`: `POST /measurements` a multipart + `save_upload`.
- [x] T003 `me/infrastructure/mongo_me_repository.py`: persistir/serializar `attachment_url`/`attachment_type`.
- [x] T004 `patients/domain/repositories.py` + `infrastructure`: `list_measurements`.
- [x] T005 `patients/application/patients_service.py`: `list_measurements`.
- [x] T006 `patients/presentation/router.py`: `GET /{patient_id}/measurements`.
- [x] T007 Tests: `test_me_service.py` (+1 caso), `test_patients_service.py` (+2 casos).

## Phase 3: Validation

- [x] T008 Suite completa → 163/163 verde.
- [x] T009 Verificación en vivo end-to-end (foto subida por paciente, leída por su nutriólogo, rechazada para un nutriólogo no relacionado).

## Evidence

- Suite completa: 163/163 verde.
- Verificación en vivo: `POST /me/measurements` con foto real (PNG) devuelve `attachment_url` resoluble; `GET /patients/{id}/measurements` del nutriólogo dueño la muestra; la URL del adjunto sirve los bytes correctos (`image/png`); un segundo nutriólogo no relacionado recibe 404. Cuentas y datos de prueba limpiados al final.
