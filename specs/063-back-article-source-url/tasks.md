# Tasks: Article Source URL

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `content_library/domain/entities.py`: `source_url` en `Article`.
- [x] T003 `schemas/content_library.py`: `source_url` en `ArticleOut`/`ArticleIn`/`ArticleUpdate`.
- [x] T004 `mongo_content_library_repository.py`: paso de `source_url` en creación y lectura.
- [x] T005 `me/infrastructure/mongo_me_repository.py` (`_article_dict`): `source_url` en la vista fusionada del paciente.
- [x] T006 `sync_medlineplus_content_library.py`: guarda `raw["url"]` como `source_url` (antes se descartaba).

## Phase 3: Validation

- [x] T007 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 225/225 verde.
- [x] T008 Re-sincronización en vivo de MedlinePlus (backfill) + verificación end-to-end (coach, paciente, autoría propia).

## Evidence

- Suite completa: 225/225 verde.
- Re-sync en vivo: "Synced 117 platform articles from MedlinePlus." → 110 artículos de plataforma, 105 con `source_url` real, 5 (los seed manuales) sin él, como se esperaba.
- `GET /content/articles/platform` (coach) y `GET /me/articles` (paciente): `source_url` presente y correcto en ambos.
- Artículo desechable creado vía `POST /content/articles` con `source_url` manual, verificado en `GET /content/articles/mine`, luego eliminado.
