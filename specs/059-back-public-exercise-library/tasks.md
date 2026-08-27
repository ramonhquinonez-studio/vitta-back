# Tasks: Public (Licensed) Exercise Library (Backend)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `mongo_exercise_library_repository.py`: `list_platform_items`, `get_platform_item`, `update_platform_item_video_url`.
- [x] T003 `domain/repositories.py`, `exercise_library_service.py`: passthroughs + `get_platform_video_url` con caché fetch-once.
- [x] T004 `presentation/router.py`: `GET /exercise-library/platform`, `GET /exercise-library/platform/{item_id}/video-url`.
- [x] T005 `app/core/config.py`: `WORKOUTX_API_KEY`.
- [x] T006 `workoutx_client.py` nuevo (`list_exercises`, `fetch_gif_bytes`).
- [x] T007 `app/core/storage.py`: `save_bytes`.
- [x] T008 `app/scripts/sync_workoutx_exercise_library.py` nuevo.
- [x] T009 `tests/test_exercise_library_service.py`: tests nuevos.
- [x] T010 (Descartado) Integración inicial contra MuscleWiki — reemplazada por completo tras confirmar que su tier gratuito no permite acceso directo a la API.

## Phase 3: Validation

- [x] T011 Suite de unittest completa → 224/224 verde.
- [x] T012 Verificación en vivo por curl contra la API real de WorkoutX: sync de 5 ejercicios reales, `GET /exercise-library/platform` confirma datos reales, `GET .../video-url` cachea en la primera llamada y la URL cacheada carga sin auth.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 224/224 verde.
- `python -m app.scripts.sync_workoutx_exercise_library --limit 5`: "Synced 5 platform exercises from WorkoutX."
- Curl en vivo contra `http://127.0.0.1:8000`: los cuatro criterios de aceptación confirmados contra datos reales. Cuenta de nutriólogo de prueba eliminada; los 5 ejercicios reales sincronizados y el GIF cacheado se conservaron (contenido real, no descartable).
