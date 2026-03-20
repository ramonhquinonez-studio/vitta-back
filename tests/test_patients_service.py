import unittest

from app.modules.patients.application.patients_service import PatientsService
from app.modules.patients.domain.entities import Patient


class _FakePatientsRepository:
    def __init__(self):
        self.patients: dict[str, Patient] = {}
        self.sequence = 1

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
