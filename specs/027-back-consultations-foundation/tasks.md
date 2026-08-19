# Tasks: Consultation Session Foundation

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `consultations/domain/`: entidades (`Consultation`, `EvaluationSnapshot`) + repositorio protocol.
- [x] T003 `mongo_consultations_repository.py`: implementación (draft resolution, merge de evaluación).
- [x] T004 `consultations_service.py`: `start`/`get`/`update`/`update_evaluation`/`update_close`/`complete`.
- [x] T005 `app/schemas/consultation.py` + `presentation/router.py`.
- [x] T006 `app/routers/consultations.py` + registro en `main.py`.
- [x] T007 `app/db/init_indexes.py`: índices de `consultations`.
- [x] T008 Tests nuevos + guardrails de router actualizados.

## Phase 3: Validation

- [x] T009 Suite completa → 96/96 verde.
- [x] T010 `curl POST /consultations/start` → crea borrador nuevo.
- [x] T011 `curl POST /consultations/start` (mismo paciente) → reanuda el mismo borrador, backfill de `appointment_id`.
- [x] T012 `curl PATCH .../evaluation` (dos llamadas parciales) → merge exacto, campos previos preservados.
- [x] T013 `curl PATCH .../close` + `POST .../complete` → cierre y congelado correctos; doble-complete → 400.
- [x] T014 `curl POST /consultations/start` tras completar → crea un borrador nuevo, no reanuda el congelado.

## Evidence

- Suite completa: 96/96, verde.
- `curl`: ciclo de vida completo verificado extremo a extremo con una cuenta y paciente de prueba desechables — inicio, reanudación, backfill de cita, autosave parcial de evaluación (peso guardado en la primera llamada, estatura en la segunda, ambos presentes al leer), notas de cierre, completado, rechazo de doble-completado, y nuevo borrador tras completar.
