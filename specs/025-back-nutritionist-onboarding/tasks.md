# Tasks: Nutritionist Onboarding — Backend Foundation

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `RegisterNutritionistIn` + `AuthService.register_nutritionist` + `POST /auth/register-nutritionist`.
- [x] T003 `NutritionistProfile`: `MacroSplit` + nuevos campos (perfil profesional, especialización, preferencias, `onboarding_completed_at`).
- [x] T004 `mongo_nutritionist_profile_repository.py`: `_to_entity` extendido + `mark_onboarding_completed`.
- [x] T005 `nutritionist_profile_service.py`: `_serialize` extendido + `complete_onboarding`.
- [x] T006 `app/schemas/nutritionist_profile.py`: `Update`/`Out` extendidos con `Literal` para campos de enum.
- [x] T007 `POST /nutritionist_profile/me/complete-onboarding`.
- [x] T008 Tests: 2 nuevos en `test_auth_service.py`, 2 nuevos en `test_nutritionist_profile_service.py`.

## Phase 3: Validation

- [x] T009 Suite completa → 68/68 verde.
- [x] T010 `curl POST /auth/register-nutritionist` → cuenta real creada, sin registro de paciente.
- [x] T011 `curl PATCH /nutritionist_profile/me` con todos los campos nuevos → reflejados correctamente.
- [x] T012 `curl POST /nutritionist_profile/me/complete-onboarding` → timestamp real asignado en servidor.

## Evidence

- Suite completa: 68/68, verde.
- `curl`: cuenta `test.onboarding.verify@nutri.app` creada con `role=nutritionist`; perfil actualizado con cédula/especializaciones/macro_split/etc.; `onboarding_completed_at` poblado tras completar.
