# Tasks: Production-Readiness Hardening

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `storage.py`: extensión derivada solo de `content_type`, nunca del filename.
- [x] T003 5 endpoints de upload: `max_size_bytes` + manejo `ValueError` → `413`.
- [x] T004 Rate limiting en `/auth/login` y `/auth/forgot-password`.
- [x] T005 `config.py`: `CORS_ORIGINS` vacío falla el arranque fuera de local.
- [x] T006 `messaging_service.py`/router: verificación de propiedad antes de subir adjuntos.
- [x] T007 `docs/modules/architecture.md` corregido (17/21 módulos migrados, no 5).
- [x] T008 `test_storage.py`: 2 tests nuevos de regresión.

## Phase 3: Validation

- [x] T009 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 227/227 verde.
- [x] T010 Verificación en vivo: ownership check (404) y fix de extensión (spoofed filename → `.jpg`), con limpieza posterior.

## Evidence

- Suite completa: 227/227 verde (225 previos + 2 nuevos).
- En vivo: `POST /patients/000.../messages/attachment` → 404 (paciente no existente/no propio); `POST /patients/{id real}/messages/attachment` con `filename=evil.html`, `content-type=image/jpeg` → guardado como `.jpg`, confirmado. Archivo de prueba eliminado tras la verificación.
