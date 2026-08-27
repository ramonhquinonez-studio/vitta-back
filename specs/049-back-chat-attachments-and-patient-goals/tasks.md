# Tasks: Chat Photo Attachments + Per-Patient Nutrition Goals

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `messaging`: `Message`/`create()`/`send_from_nutritionist` con `attachment_url`/`attachment_type` + `POST /{patient_id}/messages/attachment`.
- [x] T003 `me`: `create_message`/`send_message` con los mismos campos + `POST /me/messages/attachment`.
- [x] T004 `Patient`: 4 campos de meta nutricional (entidad, Mongo, schemas, `_serialize`).
- [x] T005 `me/infrastructure/mongo_me_repository.py::get_patient_for_user`: mismos 4 campos, para que `GET /me/profile` los exponga al propio paciente.
- [x] T006 Tests: `test_messaging_service.py` (+1), `test_me_service.py` (+1), `test_patients_service.py` (+1).

## Phase 3: Validation

- [x] T007 Suite completa → 210/210 verde.
- [x] T008 Verificación en vivo (metas nutricionales desde el nutriólogo y desde el propio paciente, adjunto de foto sin texto, rechazo de no-imagen).

## Evidence

- Suite completa: 210/210 verde.
- Verificación en vivo: 4 metas nutricionales configuradas y confirmadas en el `GET` del nutriólogo; el propio paciente registrado y vinculado vía código de invitación confirmó las mismas metas en su `GET /me/profile`; foto subida y enviada como mensaje sin texto, confirmada en ambas lecturas (`GET /patients/{id}/messages` y accesible directamente, `200 image/jpeg`); archivo no-imagen rechazado (`400`). Cuentas y datos de prueba limpiados al final.
