# Tasks: Back Config Secrets Baseline

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Config Cleanup

- [x] T002 Remover secretos reales hardcodeados.
- [x] T003 Agregar validación de placeholders inseguros en prod.
- [x] T004 Validar configuración parcial de Google OAuth.
- [x] T005 Hacer Firebase opcional cuando no exista archivo local.

## Phase 3: Documentation and Validation

- [x] T006 Documentar variables de entorno.
- [x] T007 Agregar tests de configuración.
- [x] T008 Ejecutar validación de config y registrar evidencia.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest tests.test_config_guardrails`
- `PYTHONPATH=. .venv/bin/python -m py_compile app/core/config.py app/core/notify.py`
