import unittest

from app.modules.patients.application.patients_service import PatientsService
from app.modules.patients.domain.entities import Patient


class _FakePatientsRepository:
    def __init__(self):
        self.patients: dict[str, Patient] = {}
        self.sequence = 1
        self.body_compositions: dict[str, list[dict]] = {}
        self.food_diary_entries: dict[str, list[dict]] = {}
        self.plan_assignments: dict[str, list[dict]] = {}
        self.invite_sequence = 0
        self.last_invite_patient_id = "unset"
        self.connection_codes: dict[str, str] = {}

    async def list_for_owner(self, owner_id, *, page, limit, query=None):
        items = [p for p in self.patients.values() if p.owner_id == owner_id]
        if query:
            items = [p for p in items if query.lower() in p.name.lower()]
        return items[:limit], len(items)

    async def create_for_owner(self, owner_id, payload):
        patient = Patient(
            id=str(self.sequence),
            owner_id=owner_id,
            name=payload["name"],
            age=payload.get("age"),
            sex=payload.get("sex"),
            height_cm=payload.get("height_cm"),
            allergies=list(payload.get("allergies") or []),
            notes=payload.get("notes"),
            user_id=payload.get("user_id"),
        )
        self.patients[patient.id] = patient
        self.sequence += 1
        return patient

    async def get_for_owner(self, owner_id, patient_id):
        patient = self.patients.get(patient_id)
        if patient and patient.owner_id == owner_id:
            return patient
        return None

    async def update_for_owner(self, owner_id, patient_id, payload):
        current = await self.get_for_owner(owner_id, patient_id)
        if current is None:
            return None
        updated = Patient(
            id=current.id,
            owner_id=current.owner_id,
            name=payload.get("name", current.name),
            age=payload.get("age", current.age),
            sex=payload.get("sex", current.sex),
            height_cm=payload.get("height_cm", current.height_cm),
            allergies=payload.get("allergies", current.allergies),
            notes=payload.get("notes", current.notes),
        )
        self.patients[patient_id] = updated
        return updated

    async def delete_for_owner(self, owner_id, patient_id):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return False
        del self.patients[patient_id]
        return True

    async def list_body_compositions(self, owner_id, patient_id):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return None
        return self.body_compositions.get(patient_id, [])

    async def list_food_diary_entries(self, owner_id, patient_id):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return None
        return self.food_diary_entries.get(patient_id, [])

    async def list_plan_assignments(self, owner_id, patient_id):
        patient = await self.get_for_owner(owner_id, patient_id)
        if patient is None:
            return None
        return self.plan_assignments.get(patient_id, [])

    async def create_invite_code(self, owner_id, patient_id=None):
        self.invite_sequence += 1
        self.last_invite_patient_id = patient_id
        return {"code": f"CODE{self.invite_sequence}", "expires_at": None}

    async def create_unclaimed(self, name, code):
        patient = Patient(id=str(self.sequence), owner_id=None, name=name)
        self.patients[patient.id] = patient
        self.connection_codes[code] = patient.id
        self.sequence += 1
        return patient

    async def claim_patient(self, owner_id, code):
        patient_id = self.connection_codes.get(code)
        if patient_id is None:
            return None
        patient = self.patients.get(patient_id)
        if patient is None or patient.owner_id is not None:
            return None
        updated = Patient(
            id=patient.id,
            owner_id=owner_id,
            name=patient.name,
            age=patient.age,
            sex=patient.sex,
            height_cm=patient.height_cm,
            allergies=patient.allergies,
            notes=patient.notes,
            user_id=patient.user_id,
        )
        self.patients[patient_id] = updated
        del self.connection_codes[code]
        return updated


class PatientsServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_list_patients_returns_items_and_total(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        await repository.create_for_owner("owner-1", {"name": "Maria"})
        await repository.create_for_owner("owner-1", {"name": "Mario"})

        items, total = await service.list_patients(
            "owner-1",
            page=1,
            limit=20,
            query="Mari",
        )

        self.assertEqual(total, 2)
        self.assertEqual([item.name for item in items], ["Maria", "Mario"])

    async def test_update_patient_rejects_empty_payload(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)

        with self.assertRaises(ValueError):
            await service.update_patient("owner-1", "1", {})

    async def test_list_body_compositions_returns_the_patients_scans(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        repository.body_compositions[patient.id] = [
            {"id": "bc-1", "at": None, "metrics": {"weight_kg": 68.5}}
        ]

        result = await service.list_body_compositions("owner-1", patient.id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metrics"]["weight_kg"], 68.5)

    async def test_list_body_compositions_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        with self.assertRaises(LookupError):
            await service.list_body_compositions("owner-2", patient.id)

    async def test_list_food_diary_entries_returns_the_patients_entries(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        repository.food_diary_entries[patient.id] = [
            {"id": "entry-1", "dish": "Tacos al pastor", "kcal": 450}
        ]

        result = await service.list_food_diary_entries("owner-1", patient.id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["dish"], "Tacos al pastor")

    async def test_list_food_diary_entries_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        with self.assertRaises(LookupError):
            await service.list_food_diary_entries("owner-2", patient.id)

    async def test_list_plan_assignments_returns_the_patients_history(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})
        repository.plan_assignments[patient.id] = [
            {"plan_id": "plan-2", "plan_name": "Plan B", "assigned_at": "2026-08-10"},
            {"plan_id": "plan-1", "plan_name": "Plan A", "assigned_at": "2026-08-01"},
        ]

        result = await service.list_plan_assignments("owner-1", patient.id)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["plan_name"], "Plan B")

    async def test_list_plan_assignments_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Maria"})

        with self.assertRaises(LookupError):
            await service.list_plan_assignments("owner-2", patient.id)

    async def test_create_invite_code_without_a_patient_id_delegates_directly(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)

        invite = await service.create_invite_code("owner-1")

        self.assertEqual(invite["code"], "CODE1")
        self.assertIsNone(repository.last_invite_patient_id)

    async def test_create_invite_code_for_an_existing_unlinked_patient_succeeds(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Juan"})

        invite = await service.create_invite_code("owner-1", patient_id=patient.id)

        self.assertEqual(invite["code"], "CODE1")
        self.assertEqual(repository.last_invite_patient_id, patient.id)

    async def test_create_invite_code_rejects_an_already_linked_patient(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner(
            "owner-1", {"name": "Juan", "user_id": "user-1"}
        )

        with self.assertRaises(ValueError):
            await service.create_invite_code("owner-1", patient_id=patient.id)

    async def test_create_invite_code_rejects_a_patient_not_owned(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_for_owner("owner-1", {"name": "Juan"})

        with self.assertRaises(LookupError):
            await service.create_invite_code("owner-2", patient_id=patient.id)

    async def test_claim_patient_links_the_owner_and_consumes_the_code(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        patient = await repository.create_unclaimed("Sola Paciente", "SOLO2026")

        claimed = await service.claim_patient("owner-1", "SOLO2026")

        self.assertEqual(claimed.id, patient.id)
        self.assertEqual(claimed.owner_id, "owner-1")
        self.assertNotIn("SOLO2026", repository.connection_codes)

    async def test_claim_patient_rejects_an_unknown_code(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)

        with self.assertRaises(LookupError):
            await service.claim_patient("owner-1", "NOPE0000")

    async def test_claim_patient_rejects_a_code_already_claimed(self):
        repository = _FakePatientsRepository()
        service = PatientsService(repository)
        await repository.create_unclaimed("Sola Paciente", "SOLO2026")
        await service.claim_patient("owner-1", "SOLO2026")

        with self.assertRaises(LookupError):
            await service.claim_patient("owner-2", "SOLO2026")
