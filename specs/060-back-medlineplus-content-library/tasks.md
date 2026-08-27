# Tasks: MedlinePlus-Synced Platform Articles (Backend)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/scripts/sync_medlineplus_content_library.py` nuevo (`_GROUPS`, `_fetch_group`, `_SummaryParser`, `_parse_section`, `sync`, `main`).

## Phase 3: Validation

- [x] T003 Suite de unittest completa → 224/224 verde (sin cambios de código existente).
- [x] T004 Ejecución en vivo contra la API real de MedlinePlus (2 grupos iniciales): 89 artículos procesados, 87 documentos distintos sincronizados.
- [x] T005 Verificación en vivo por curl: `GET /me/articles` contra una cuenta de paciente de prueba (sin asignar) confirma 92 artículos totales (5 curados a mano + 87 de MedlinePlus), categoría/título/descripción/secciones/atribución correctos en una muestra.
- [x] T006 `_GROUPS` ampliado a 4 grupos (Diabetes mellitus, Aptitud física y ejercicio) tras muestrear títulos reales y descartar grupos clínicos genéricos no relevantes. Re-ejecución: 117 procesados, 110 documentos distintos.

## Evidence

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`: 224/224 verde (ambas ejecuciones).
- `python -m app.scripts.sync_medlineplus_content_library`: "Synced 89 platform articles..." luego "Synced 117 platform articles from MedlinePlus."
- Curl en vivo contra `http://127.0.0.1:8000`: los cuatro criterios de aceptación confirmados tras la primera sincronización. Conteo directo por categoría en Mongo tras la ampliación: 110 totales (54 nutrición, 23 bienestar, 19 diabetes, 9 ejercicio, 5 curados a mano). Cuenta de paciente de prueba eliminada; todos los artículos reales se conservaron (contenido real, no descartable).
