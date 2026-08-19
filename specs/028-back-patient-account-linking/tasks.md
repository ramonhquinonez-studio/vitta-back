# Tasks: Patient-Scoped Invite Codes (Account Linking)

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `patients/domain/entities.py`: `Patient.user_id`.
- [x] T003 `patients/domain/repositories.py` + `mongo_patients_repository.py`: `create_invite_code` con `patient_id` opcional, `_to_entity` lee `user_id`.
- [x] T004 `patients_service.py`: validación de paciente propio/no vinculado.
- [x] T005 `app/schemas/patients.py` + `presentation/router.py`: `PatientOut.user_id`, `POST /{patient_id}/invite-code`.
- [x] T006 `auth/domain/repositories.py` + `mongo_auth_repository.py`: `get_invite_code` con `patient_id`, `link_user_to_patient`.
- [x] T007 `auth_service.py`: `register()` vincula en vez de duplicar cuando aplica.
- [x] T008 Tests nuevos.

## Phase 3: Validation

- [x] T009 Suite completa → 92/92 verde.
- [x] T010 `curl` ciclo completo: crear paciente → generar código escopado → verificar `user_id: null` → registrar → verificar mismo id con `user_id` set → confirmar sin duplicado en el roster → segundo intento de invite → 400 → login exitoso → flujo sin escopar sigue creando paciente nuevo.

## Evidence

- Suite completa: 92/92, verde.
- `curl`: paciente "Roberto Diaz" creado sin cuenta → código escopado generado → registrado con `roberto.diaz.test@nutri.app` → mismo `id` ahora con `user_id` poblado, roster con total=1 (no 2) → segundo invite sobre el mismo paciente → 400 "Patient already has a linked account" → login exitoso confirmado → invite sin escopar para "Nueva Paciente" siguió creando un registro nuevo, total=2 en el roster.
