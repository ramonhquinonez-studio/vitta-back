# Tasks: Patient Self-Registration + Nutritionist Claim by Connection Code

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `patients/domain/entities.py`: `owner_id` opcional, reordenado.
- [x] T003 `mongo_patients_repository.py`: `_to_entity` tolera `owner_id` nulo; `claim_patient`.
- [x] T004 `patients/domain/repositories.py` + `patients_service.py`: `claim_patient`.
- [x] T005 `app/schemas/patients.py`: `PatientOut.owner_id` opcional, `ClaimPatientIn`.
- [x] T006 `patients/presentation/router.py`: `POST /patients/claim`.
- [x] T007 `auth/domain/repositories.py` + `mongo_auth_repository.py`: `create_unowned_patient_for_user`.
- [x] T008 `auth_service.py`: `register()` con `invite_code` opcional.
- [x] T009 `app/schemas/auth.py`: `RegisterIn.invite_code` opcional.
- [x] T010 `mongo_me_repository.py`: `get_patient_for_user` expone `connection_code`.
- [x] T011 `app/db/init_indexes.py`: índice único sparse en `connection_code`.
- [x] T012 Tests nuevos (`test_auth_service.py`, `test_patients_service.py`).

## Phase 3: Validation

- [x] T013 Suite completa → 100/100 verde.
- [x] T014 `curl` ciclo completo: registro sin código → `owner_id: null` + `connection_code` real → registro de nutriólogo → roster vacío → claim (minúsculas) → mismo id, roster=1 → perfil del paciente con `connection_code: null` → re-claim mismo código → 404 → código desconocido → 404.

## Evidence

- Suite completa: 100/100, verde.
- `curl`: paciente "Vista Previa Paciente" auto-registrado sin código → `owner_id: null`, `connection_code: "84UPRTCY"`. Nutriólogo "Dra. Claim Test" registrado → roster total=0. `POST /patients/claim` con `{"code": "84dvhtuv"}` (minúsculas) → mismo `id` del paciente, `owner_id` del nutriólogo, roster total=1. `GET /me/profile` del paciente tras el claim → `connection_code: null`. Reintento del mismo código → 404 "Invalid or already-claimed connection code". Código inventado → 404 idéntico.
