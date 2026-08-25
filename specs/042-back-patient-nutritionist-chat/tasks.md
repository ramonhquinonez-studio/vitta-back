# Tasks: Patient-Nutritionist Chat

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `messaging/domain`: entidad + Protocol.
- [x] T003 `messaging/infrastructure/mongo_messaging_repository.py`.
- [x] T004 `messaging/application/messaging_service.py`.
- [x] T005 `schemas/messaging.py` + `messaging/presentation/router.py` (con push al enviar).
- [x] T006 `routers/messaging.py` wrapper + wiring en `main.py`.
- [x] T007 Índice compuesto en `messages`.
- [x] T008 `me` module: `list_messages`/`create_message`/`send_message`/`get_my_patient_record` + endpoints `GET/POST /me/messages` (con push al enviar).
- [x] T009 Tests: `test_messaging_service.py` (5 casos), `test_me_service.py` (+4 casos).

## Phase 3: Validation

- [x] T010 Suite completa → 160/160 verde.
- [x] T011 Verificación en vivo end-to-end (ambas direcciones, aislamiento entre tenants, filtro `since`).

## Evidence

- Suite completa: 160/160 verde.
- Verificación en vivo: paciente→nutriólogo y nutriólogo→paciente confirmados con curl real; un segundo nutriólogo no relacionado recibe 404 al intentar leer el hilo; `since` en el futuro devuelve lista vacía. Cuentas de prueba limpiadas al final.
