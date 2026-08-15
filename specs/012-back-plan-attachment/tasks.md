# Tasks: Plan Attachment

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/schemas/plan.py`: `PlanOut.attachment_url`/`attachment_type`.
- [x] T003 `app/modules/plans/domain/repositories.py`: `set_attachment_for_owner` en el protocolo.
- [x] T004 `mongo_plans_repository.py`: `_serialize` + `set_attachment_for_owner`.
- [x] T005 `plans_service.py`: `set_attachment`.
- [x] T006 `plans/presentation/router.py`: `POST /plans/{plan_id}/attachment`.
- [x] T007 `mongo_me_repository.py#get_active_plan`: incluir `attachment_url`/`attachment_type`.
- [x] T008 `tests/test_plans_service.py`: fake repo + tests nuevos.

## Phase 3: Validation

- [x] T009 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 31/31 verde.
- [x] T010 Manual: `POST /plans/{id}/attachment` contra backend real con el PDF real del usuario; verificado `GET /me/plan/active` y la URL `/uploads/...` sirviendo el archivo.

## Evidence

- Backend suite completa en verde (31 tests, antes 29).
- `curl -X POST .../plans/{id}/attachment -F file=@PDF.pdf` → 200, `attachment_url`/`attachment_type` presentes.
- `curl .../uploads/plans/{id}/{file}.pdf` → 200 `application/pdf`, 212896 bytes.
