# Tasks: Video/File Chat Attachments (Backend)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `messaging/presentation/router.py`: gate de content-type ampliado.
- [x] T003 `me/presentation/router.py`: gate de content-type ampliado (idéntico).

## Phase 3: Validation

- [x] T004 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 218/218 verde.
- [x] T005 Verificación en vivo por curl: `.mp4`/`.pdf` aceptados en ambos endpoints, `.txt` rechazado (400) en ambos. Limpieza de datos QA.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 218/218 verde, sin regresiones.
- curl en vivo: nutritionist-side `.mp4`→200 (`content_type: video/mp4`), `.pdf`→200 (`content_type: application/pdf`), `.txt`→400; patient-side `.mp4`→200, `.txt`→400 (`"El archivo debe ser una imagen, video o PDF."`). Datos de prueba (nutritionist + patient + chart) limpiados con script directo de Motor.
