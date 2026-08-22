# Tasks: Nutritionist-Authored Content Library

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `content_library/domain/entities.py`: `Article` gana `owner_id`, `video_url`.
- [x] T003 `content_library/domain/repositories.py` + `mongo_content_library_repository.py`: `list_for_owner`/`create_for_owner`/`update_for_owner`/`delete_for_owner`, mismo patrón que `recipes`.
- [x] T004 `content_library_service.py`: `list_my_articles`/`create`/`update`/`delete`, validación título + (texto o video).
- [x] T005 `app/schemas/content_library.py`: `ArticleOut` + `ArticleIn`/`ArticleUpdate`/`ArticleSectionIn`.
- [x] T006 `content_library/presentation/router.py`: `GET /content/articles/mine`, `POST/PATCH/DELETE /content/articles...`.
- [x] T007 `me` module: `list_articles` en domain/infra/application/router — `GET /me/articles`, fusiona plataforma + nutriólogo propio.
- [x] T008 Tests: 5 nuevos en `test_content_library_service.py`, 2 nuevos en `test_me_service.py`.

## Phase 3: Validation

- [x] T009 Suite completa → 121/121 verde.
- [x] T010 Verificación manual en vivo contra el backend corriendo: cuenta de nutriólogo y paciente de prueba (vinculado por código de invitación), creación de artículo de texto y de video, `GET /content/articles/mine`, `PATCH`, `DELETE`, validación 400 sin texto/video, y `GET /me/articles` del paciente confirmando la fusión exacta (5 de plataforma + 2 propios). Datos de prueba (artículos) eliminados tras verificar.

## Evidence

- Suite completa: 121/121, verde (114 previos + 7 nuevos).
- Verificación en vivo con `curl` contra `http://127.0.0.1:8000`, documentada en la conversación: creación/listado/edición/borrado de artículos propios, y fusión correcta plataforma+nutriólogo en `/me/articles` para un paciente vinculado vía invite code.
